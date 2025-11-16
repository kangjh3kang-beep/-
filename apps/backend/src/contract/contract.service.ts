import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { Decimal } from '@prisma/client/runtime/library';

@Injectable()
export class ContractService {
  constructor(private prisma: PrismaService) {}

  async create(tenantId: string, userId: string, data: any) {
    const { projectId, customerName, contractAmount, ...rest } = data;

    // Generate contract number
    const count = await this.prisma.contract.count({ where: { tenantId } });
    const contractNumber = `CT-${new Date().getFullYear()}-${String(count + 1).padStart(5, '0')}`;

    return this.prisma.contract.create({
      data: {
        contractNumber,
        tenantId,
        projectId,
        customerName,
        contractAmount,
        createdById: userId,
        ...rest,
      },
      include: {
        project: true,
        salesperson: { select: { id: true, name: true, email: true } },
      },
    });
  }

  async findAll(
    tenantId: string,
    filters?: {
      projectId?: string;
      status?: string;
      salespersonId?: string;
      search?: string;
      startDate?: Date;
      endDate?: Date;
    },
  ) {
    const where: any = { tenantId };

    if (filters?.projectId) where.projectId = filters.projectId;
    if (filters?.status) where.status = filters.status;
    if (filters?.salespersonId) where.salespersonId = filters.salespersonId;
    if (filters?.search) {
      where.OR = [
        { contractNumber: { contains: filters.search } },
        { customerName: { contains: filters.search } },
        { customerPhone: { contains: filters.search } },
      ];
    }
    if (filters?.startDate || filters?.endDate) {
      where.createdAt = {};
      if (filters.startDate) where.createdAt.gte = filters.startDate;
      if (filters.endDate) where.createdAt.lte = filters.endDate;
    }

    return this.prisma.contract.findMany({
      where,
      include: {
        project: { select: { id: true, name: true, code: true } },
        salesperson: { select: { id: true, name: true } },
      },
      orderBy: { createdAt: 'desc' },
    });
  }

  async findOne(id: string, tenantId: string) {
    return this.prisma.contract.findFirst({
      where: { id, tenantId },
      include: {
        project: true,
        salesperson: true,
        createdBy: true,
      },
    });
  }

  async update(id: string, data: any) {
    return this.prisma.contract.update({
      where: { id },
      data,
    });
  }

  async updateStatus(id: string, status: string) {
    return this.prisma.contract.update({
      where: { id },
      data: { status },
    });
  }

  async uploadDocument(id: string, documentUrl: string) {
    return this.prisma.contract.update({
      where: { id },
      data: { documentUrl },
    });
  }

  async signContract(id: string, signedDocumentUrl: string, recordingUrl?: string) {
    return this.prisma.contract.update({
      where: { id },
      data: {
        signedDocumentUrl,
        signedAt: new Date(),
        recordingUrl,
        status: 'SIGNED',
      },
    });
  }

  async getStatistics(tenantId: string, projectId?: string) {
    const where: any = { tenantId };
    if (projectId) where.projectId = projectId;

    // Get status counts
    const statusCounts = await this.prisma.contract.groupBy({
      by: ['status'],
      where,
      _count: true,
    });

    // Get total contract amount
    const totalAmount = await this.prisma.contract.aggregate({
      where,
      _sum: { contractAmount: true },
    });

    // Get signed contract amount
    const signedAmount = await this.prisma.contract.aggregate({
      where: { ...where, status: 'SIGNED' },
      _sum: { contractAmount: true },
    });

    // Monthly contracts
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

    const monthlyContracts = await this.prisma.contract.count({
      where: {
        ...where,
        createdAt: { gte: thirtyDaysAgo },
      },
    });

    // Top salespeople
    const topSalespeople = await this.prisma.contract.groupBy({
      by: ['salespersonId'],
      where: { ...where, salespersonId: { not: null } },
      _count: true,
      _sum: { contractAmount: true },
      orderBy: { _count: { salespersonId: 'desc' } },
      take: 5,
    });

    const salespeople = await Promise.all(
      topSalespeople.map(async (item) => {
        const user = await this.prisma.user.findUnique({
          where: { id: item.salespersonId },
          select: { id: true, name: true, email: true },
        });
        return {
          ...user,
          contractCount: item._count,
          totalAmount: item._sum.contractAmount || 0,
        };
      }),
    );

    return {
      total: statusCounts.reduce((sum, item) => sum + item._count, 0),
      byStatus: statusCounts.reduce(
        (acc, item) => {
          acc[item.status.toLowerCase()] = item._count;
          return acc;
        },
        {} as Record<string, number>,
      ),
      totalAmount: totalAmount._sum.contractAmount || 0,
      signedAmount: signedAmount._sum.contractAmount || 0,
      monthlyContracts,
      topSalespeople: salespeople.filter((s) => s !== null),
    };
  }

  async getContractsByMonth(tenantId: string, year: number, projectId?: string) {
    const where: any = { tenantId };
    if (projectId) where.projectId = projectId;

    const startDate = new Date(year, 0, 1);
    const endDate = new Date(year, 11, 31);

    const contracts = await this.prisma.contract.findMany({
      where: {
        ...where,
        createdAt: {
          gte: startDate,
          lte: endDate,
        },
      },
      select: {
        createdAt: true,
        contractAmount: true,
        status: true,
      },
    });

    const byMonth = Array.from({ length: 12 }, (_, i) => ({
      month: i + 1,
      count: 0,
      amount: new Decimal(0),
      signed: 0,
    }));

    contracts.forEach((contract) => {
      const month = contract.createdAt.getMonth();
      byMonth[month].count++;
      byMonth[month].amount = byMonth[month].amount.plus(contract.contractAmount);
      if (contract.status === 'SIGNED') byMonth[month].signed++;
    });

    return byMonth;
  }
}

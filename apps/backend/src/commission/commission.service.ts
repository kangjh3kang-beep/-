import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class CommissionService {
  constructor(private prisma: PrismaService) {}

  async createCommission(tenantId: string, data: any) {
    return this.prisma.commission.create({
      data: {
        ...data,
        tenantId,
      },
      include: {
        contract: true,
        user: { select: { id: true, name: true, email: true } },
      },
    });
  }

  async getCommissions(
    tenantId: string,
    filters?: {
      userId?: string;
      contractId?: string;
      agencyId?: string;
      departmentId?: string;
      teamId?: string;
      status?: string;
      type?: string;
    },
  ) {
    const where: any = { tenantId };

    if (filters?.userId) where.userId = filters.userId;
    if (filters?.contractId) where.contractId = filters.contractId;
    if (filters?.agencyId) where.agencyId = filters.agencyId;
    if (filters?.departmentId) where.departmentId = filters.departmentId;
    if (filters?.teamId) where.teamId = filters.teamId;
    if (filters?.status) where.status = filters.status;
    if (filters?.type) where.type = filters.type;

    return this.prisma.commission.findMany({
      where,
      include: {
        contract: { select: { id: true, contractNumber: true, customerName: true } },
        user: { select: { id: true, name: true, email: true } },
      },
      orderBy: { createdAt: 'desc' },
    });
  }

  async getCommissionById(id: string, tenantId: string) {
    return this.prisma.commission.findFirst({
      where: { id, tenantId },
      include: {
        contract: true,
        user: {
          select: {
            id: true,
            name: true,
            email: true,
            agency: true,
            department: true,
            team: true,
          },
        },
      },
    });
  }

  async updateCommission(id: string, data: any) {
    return this.prisma.commission.update({
      where: { id },
      data,
    });
  }

  async approveCommission(id: string, approvedBy: string) {
    return this.prisma.commission.update({
      where: { id },
      data: {
        status: 'APPROVED',
        notes: `Approved by ${approvedBy}`,
      },
    });
  }

  async payCommission(id: string, paidBy: string) {
    return this.prisma.commission.update({
      where: { id },
      data: {
        status: 'PAID',
        paidAt: new Date(),
        paidBy,
      },
    });
  }

  async getCommissionStatistics(tenantId: string) {
    const [total, byStatus, byType, totalAmount] = await Promise.all([
      this.prisma.commission.count({ where: { tenantId } }),
      this.prisma.commission.groupBy({
        by: ['status'],
        where: { tenantId },
        _count: true,
        _sum: { amount: true },
      }),
      this.prisma.commission.groupBy({
        by: ['type'],
        where: { tenantId },
        _count: true,
        _sum: { amount: true },
      }),
      this.prisma.commission.aggregate({
        where: { tenantId },
        _sum: { amount: true },
      }),
    ]);

    return {
      total,
      byStatus: byStatus.reduce((acc, item) => {
        acc[item.status] = {
          count: item._count,
          amount: item._sum.amount || 0,
        };
        return acc;
      }, {}),
      byType: byType.reduce((acc, item) => {
        acc[item.type] = {
          count: item._count,
          amount: item._sum.amount || 0,
        };
        return acc;
      }, {}),
      totalAmount: totalAmount._sum.amount || 0,
    };
  }

  async getUserCommissionSummary(tenantId: string, userId: string) {
    const [total, pending, approved, paid, totalAmount, paidAmount] = await Promise.all([
      this.prisma.commission.count({ where: { tenantId, userId } }),
      this.prisma.commission.count({ where: { tenantId, userId, status: 'PENDING' } }),
      this.prisma.commission.count({ where: { tenantId, userId, status: 'APPROVED' } }),
      this.prisma.commission.count({ where: { tenantId, userId, status: 'PAID' } }),
      this.prisma.commission.aggregate({
        where: { tenantId, userId },
        _sum: { amount: true },
      }),
      this.prisma.commission.aggregate({
        where: { tenantId, userId, status: 'PAID' },
        _sum: { amount: true },
      }),
    ]);

    return {
      total,
      pending,
      approved,
      paid,
      totalAmount: totalAmount._sum.amount || 0,
      paidAmount: paidAmount._sum.amount || 0,
      unpaidAmount: (totalAmount._sum.amount || 0) - (paidAmount._sum.amount || 0),
    };
  }
}

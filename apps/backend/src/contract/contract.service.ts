import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

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

  async findAll(tenantId: string, projectId?: string) {
    return this.prisma.contract.findMany({
      where: {
        tenantId,
        ...(projectId && { projectId }),
      },
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
}

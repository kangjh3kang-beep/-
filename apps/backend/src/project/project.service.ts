import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class ProjectService {
  constructor(private prisma: PrismaService) {}

  async create(tenantId: string, userId: string, data: any) {
    return this.prisma.project.create({
      data: {
        ...data,
        tenantId,
        createdById: userId,
      },
      include: {
        createdBy: { select: { id: true, name: true, email: true } },
        manager: { select: { id: true, name: true, email: true } },
      },
    });
  }

  async findAll(tenantId: string) {
    return this.prisma.project.findMany({
      where: { tenantId },
      include: {
        createdBy: { select: { id: true, name: true } },
        manager: { select: { id: true, name: true } },
        _count: {
          select: {
            contracts: true,
            lands: true,
            constructions: true,
          },
        },
      },
      orderBy: { createdAt: 'desc' },
    });
  }

  async findOne(id: string, tenantId: string) {
    return this.prisma.project.findFirst({
      where: { id, tenantId },
      include: {
        createdBy: true,
        manager: true,
        contracts: { take: 10, orderBy: { createdAt: 'desc' } },
        lands: { take: 10 },
        constructions: { take: 10, orderBy: { createdAt: 'desc' } },
      },
    });
  }

  async update(id: string, tenantId: string, data: any) {
    return this.prisma.project.update({
      where: { id },
      data,
    });
  }

  async delete(id: string) {
    return this.prisma.project.delete({
      where: { id },
    });
  }
}

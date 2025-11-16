import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class ConstructionService {
  constructor(private prisma: PrismaService) {}

  async create(tenantId: string, data: any) {
    return this.prisma.construction.create({
      data: {
        ...data,
        tenantId,
      },
      include: {
        project: { select: { id: true, name: true } },
      },
    });
  }

  async findAll(tenantId: string, projectId: string) {
    return this.prisma.construction.findMany({
      where: {
        tenantId,
        projectId,
      },
      include: {
        project: { select: { id: true, name: true } },
      },
      orderBy: { plannedStartDate: 'asc' },
    });
  }

  async findOne(id: string, tenantId: string) {
    return this.prisma.construction.findFirst({
      where: { id, tenantId },
      include: {
        project: true,
      },
    });
  }

  async update(id: string, data: any) {
    return this.prisma.construction.update({
      where: { id },
      data,
    });
  }

  async updateProgress(id: string, actualProgress: number) {
    return this.prisma.construction.update({
      where: { id },
      data: { actualProgress },
    });
  }
}

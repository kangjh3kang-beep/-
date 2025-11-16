import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class LandService {
  constructor(private prisma: PrismaService) {}

  async create(tenantId: string, data: any) {
    return this.prisma.land.create({
      data: {
        ...data,
        tenantId,
      },
      include: {
        project: { select: { id: true, name: true } },
      },
    });
  }

  async findAll(tenantId: string, projectId?: string) {
    return this.prisma.land.findMany({
      where: {
        tenantId,
        ...(projectId && { projectId }),
      },
      include: {
        project: { select: { id: true, name: true } },
      },
      orderBy: { createdAt: 'desc' },
    });
  }

  async findOne(id: string, tenantId: string) {
    return this.prisma.land.findFirst({
      where: { id, tenantId },
      include: {
        project: true,
      },
    });
  }

  async update(id: string, data: any) {
    return this.prisma.land.update({
      where: { id },
      data,
    });
  }

  async delete(id: string) {
    return this.prisma.land.delete({
      where: { id },
    });
  }
}

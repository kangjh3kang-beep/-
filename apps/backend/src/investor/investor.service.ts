import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class InvestorService {
  constructor(private prisma: PrismaService) {}

  async create(tenantId: string, data: any) {
    return this.prisma.investor.create({
      data: {
        ...data,
        tenantId,
      },
    });
  }

  async findAll(tenantId: string) {
    return this.prisma.investor.findMany({
      where: { tenantId },
      include: {
        _count: {
          select: { nfts: true },
        },
      },
      orderBy: { createdAt: 'desc' },
    });
  }

  async findOne(id: string, tenantId: string) {
    return this.prisma.investor.findFirst({
      where: { id, tenantId },
      include: {
        nfts: true,
      },
    });
  }

  // NFT operations
  async createNFT(tenantId: string, data: any) {
    return this.prisma.nFT.create({
      data: {
        ...data,
        tenantId,
      },
    });
  }

  async getNFTs(tenantId: string) {
    return this.prisma.nFT.findMany({
      where: { tenantId },
      include: {
        investor: { select: { id: true, name: true, email: true } },
      },
    });
  }
}

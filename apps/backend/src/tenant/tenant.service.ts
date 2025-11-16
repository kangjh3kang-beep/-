import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { CreateTenantDto } from './dto/create-tenant.dto';

@Injectable()
export class TenantService {
  constructor(private prisma: PrismaService) {}

  async create(createTenantDto: CreateTenantDto) {
    const { name, slug, domain, plan } = createTenantDto;

    const tenant = await this.prisma.tenant.create({
      data: {
        name,
        slug,
        domain,
        plan: plan || 'BASIC',
        status: 'TRIAL',
      },
    });

    return tenant;
  }

  async findAll() {
    return this.prisma.tenant.findMany({
      include: {
        _count: {
          select: {
            users: true,
            projects: true,
            contracts: true,
          },
        },
      },
    });
  }

  async findOne(id: string) {
    return this.prisma.tenant.findUnique({
      where: { id },
      include: {
        _count: {
          select: {
            users: true,
            projects: true,
            contracts: true,
            lands: true,
            investors: true,
          },
        },
      },
    });
  }

  async update(id: string, data: any) {
    return this.prisma.tenant.update({
      where: { id },
      data,
    });
  }
}

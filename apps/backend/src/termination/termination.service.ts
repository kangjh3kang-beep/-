import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class TerminationService {
  constructor(private prisma: PrismaService) {}

  async issueCertificate(tenantId: string, userId: string, issuedBy: string, data: any) {
    // Get user contract statistics
    const contracts = await this.prisma.contract.findMany({
      where: {
        tenantId,
        salespersonId: userId,
        status: 'SIGNED',
      },
      select: {
        contractAmount: true,
      },
    });

    const totalContracts = contracts.length;
    const totalAmount = contracts.reduce((sum, c) => sum + Number(c.contractAmount), 0);

    // Generate certificate number
    const count = await this.prisma.terminationCertificate.count({ where: { tenantId } });
    const certificateNumber = `TC-${new Date().getFullYear()}-${String(count + 1).padStart(5, '0')}`;

    // Get user org info
    const user = await this.prisma.user.findUnique({
      where: { id: userId },
      include: {
        agency: true,
        department: true,
        team: true,
      },
    });

    return this.prisma.terminationCertificate.create({
      data: {
        tenantId,
        userId,
        certificateNumber,
        agencyName: user.agency?.name,
        departmentName: user.department?.name,
        teamName: user.team?.name,
        totalContracts,
        totalAmount,
        issuedBy,
        ...data,
      },
      include: {
        user: { select: { id: true, name: true, email: true, phone: true } },
      },
    });
  }

  async getCertificates(tenantId: string, userId?: string) {
    return this.prisma.terminationCertificate.findMany({
      where: {
        tenantId,
        ...(userId && { userId }),
      },
      include: {
        user: { select: { id: true, name: true, email: true } },
      },
      orderBy: { issuedAt: 'desc' },
    });
  }

  async getCertificateById(id: string, tenantId: string) {
    return this.prisma.terminationCertificate.findFirst({
      where: { id, tenantId },
      include: {
        user: {
          select: {
            id: true,
            name: true,
            email: true,
            phone: true,
            agency: true,
            department: true,
            team: true,
          },
        },
      },
    });
  }

  async terminateUser(userId: string, reason: string) {
    return this.prisma.user.update({
      where: { id: userId },
      data: {
        status: 'TERMINATED',
        terminatedAt: new Date(),
        terminationReason: reason,
      },
    });
  }
}

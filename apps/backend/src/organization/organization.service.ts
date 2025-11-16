import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class OrganizationService {
  constructor(private prisma: PrismaService) {}

  // ============================================
  // AGENCY (대행사)
  // ============================================

  async createAgency(tenantId: string, data: any) {
    return this.prisma.agency.create({
      data: {
        ...data,
        tenantId,
      },
    });
  }

  async getAgencies(tenantId: string) {
    return this.prisma.agency.findMany({
      where: { tenantId },
      include: {
        parentAgency: true,
        subAgencies: true,
        departments: { include: { _count: { select: { teams: true, users: true } } } },
        _count: { select: { users: true } },
      },
      orderBy: { createdAt: 'desc' },
    });
  }

  async getAgencyById(id: string, tenantId: string) {
    return this.prisma.agency.findFirst({
      where: { id, tenantId },
      include: {
        parentAgency: true,
        subAgencies: true,
        departments: {
          include: {
            teams: true,
            users: true,
          },
        },
        users: true,
      },
    });
  }

  async updateAgency(id: string, data: any) {
    return this.prisma.agency.update({
      where: { id },
      data,
    });
  }

  // ============================================
  // DEPARTMENT (본부)
  // ============================================

  async createDepartment(tenantId: string, data: any) {
    return this.prisma.department.create({
      data: {
        ...data,
        tenantId,
      },
    });
  }

  async getDepartments(tenantId: string, agencyId?: string) {
    return this.prisma.department.findMany({
      where: {
        tenantId,
        ...(agencyId && { agencyId }),
      },
      include: {
        agency: true,
        teams: { include: { _count: { select: { users: true } } } },
        _count: { select: { users: true } },
      },
      orderBy: { createdAt: 'desc' },
    });
  }

  async getDepartmentById(id: string, tenantId: string) {
    return this.prisma.department.findFirst({
      where: { id, tenantId },
      include: {
        agency: true,
        teams: { include: { users: true } },
        users: true,
      },
    });
  }

  async updateDepartment(id: string, data: any) {
    return this.prisma.department.update({
      where: { id },
      data,
    });
  }

  // ============================================
  // TEAM (팀)
  // ============================================

  async createTeam(tenantId: string, data: any) {
    return this.prisma.team.create({
      data: {
        ...data,
        tenantId,
      },
    });
  }

  async getTeams(tenantId: string, departmentId?: string) {
    return this.prisma.team.findMany({
      where: {
        tenantId,
        ...(departmentId && { departmentId }),
      },
      include: {
        department: { include: { agency: true } },
        _count: { select: { users: true } },
      },
      orderBy: { createdAt: 'desc' },
    });
  }

  async getTeamById(id: string, tenantId: string) {
    return this.prisma.team.findFirst({
      where: { id, tenantId },
      include: {
        department: { include: { agency: true } },
        users: true,
      },
    });
  }

  async updateTeam(id: string, data: any) {
    return this.prisma.team.update({
      where: { id },
      data,
    });
  }

  // ============================================
  // STATISTICS (조직별 통계)
  // ============================================

  async getAgencyStatistics(tenantId: string, agencyId: string) {
    const [contracts, revenue, users] = await Promise.all([
      this.prisma.contract.count({
        where: {
          tenantId,
          salesperson: { agencyId },
        },
      }),
      this.prisma.contract.aggregate({
        where: {
          tenantId,
          salesperson: { agencyId },
          status: 'SIGNED',
        },
        _sum: { contractAmount: true },
      }),
      this.prisma.user.count({
        where: { tenantId, agencyId },
      }),
    ]);

    return {
      totalContracts: contracts,
      totalRevenue: revenue._sum.contractAmount || 0,
      totalUsers: users,
    };
  }

  async getDepartmentStatistics(tenantId: string, departmentId: string) {
    const [contracts, revenue, users] = await Promise.all([
      this.prisma.contract.count({
        where: {
          tenantId,
          salesperson: { departmentId },
        },
      }),
      this.prisma.contract.aggregate({
        where: {
          tenantId,
          salesperson: { departmentId },
          status: 'SIGNED',
        },
        _sum: { contractAmount: true },
      }),
      this.prisma.user.count({
        where: { tenantId, departmentId },
      }),
    ]);

    return {
      totalContracts: contracts,
      totalRevenue: revenue._sum.contractAmount || 0,
      totalUsers: users,
    };
  }

  async getTeamStatistics(tenantId: string, teamId: string) {
    const [contracts, revenue, users] = await Promise.all([
      this.prisma.contract.count({
        where: {
          tenantId,
          salesperson: { teamId },
        },
      }),
      this.prisma.contract.aggregate({
        where: {
          tenantId,
          salesperson: { teamId },
          status: 'SIGNED',
        },
        _sum: { contractAmount: true },
      }),
      this.prisma.user.count({
        where: { tenantId, teamId },
      }),
    ]);

    return {
      totalContracts: contracts,
      totalRevenue: revenue._sum.contractAmount || 0,
      totalUsers: users,
    };
  }

  async getUserContractStats(tenantId: string, userId: string) {
    const [contracts, revenue] = await Promise.all([
      this.prisma.contract.count({
        where: {
          tenantId,
          salespersonId: userId,
        },
      }),
      this.prisma.contract.aggregate({
        where: {
          tenantId,
          salespersonId: userId,
          status: 'SIGNED',
        },
        _sum: { contractAmount: true },
      }),
    ]);

    return {
      totalContracts: contracts,
      totalRevenue: revenue._sum.contractAmount || 0,
    };
  }
}

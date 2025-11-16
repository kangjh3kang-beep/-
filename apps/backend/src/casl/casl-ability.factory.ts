import { Injectable } from '@nestjs/common';
import { AbilityBuilder, PureAbility } from '@casl/ability';
import { PrismaQuery, Subjects, createPrismaAbility } from '@casl/prisma';
import { User, Project, Contract, Tenant } from '@satongpaltang/database';

type AppSubjects = Subjects<{
  User: User;
  Project: Project;
  Contract: Contract;
  Tenant: Tenant;
}> | 'all';

export type AppAbility = PureAbility<[string, AppSubjects], PrismaQuery>;

@Injectable()
export class CaslAbilityFactory {
  createForUser(user: any) {
    const { can, cannot, build } = new AbilityBuilder<AppAbility>(createPrismaAbility);

    // Role hierarchy levels:
    // 0=SYSTEM_ADMIN, 10=TENANT_ADMIN, 20=CM, 30=PM, 40=DIRECTOR, 50=MANAGER, 60=SALESPERSON, 70=CUSTOMER
    const roleLevel = user.role?.level || 70;

    // System Admin - full access
    if (roleLevel === 0) {
      can('manage', 'all');
      return build();
    }

    // Tenant Admin - manage all within tenant
    if (roleLevel === 10) {
      can('manage', 'all', { tenantId: user.tenantId });
      cannot('delete', 'Tenant');
      return build();
    }

    // CM/PM - project and contract management
    if (roleLevel <= 30) {
      can(['read', 'create', 'update'], 'Project', { tenantId: user.tenantId });
      can(['read', 'create', 'update'], 'Contract', { tenantId: user.tenantId });
      can('read', 'User', { tenantId: user.tenantId });
      return build();
    }

    // Director/Manager - read most, create/update some
    if (roleLevel <= 50) {
      can('read', 'all', { tenantId: user.tenantId });
      can(['create', 'update'], 'Contract', { tenantId: user.tenantId });
      return build();
    }

    // Salesperson - limited access
    if (roleLevel <= 60) {
      can('read', 'Project', { tenantId: user.tenantId });
      can(['read', 'create'], 'Contract', {
        tenantId: user.tenantId,
        salespersonId: user.id,
      });
      return build();
    }

    // Customer - very limited
    can('read', 'Contract', { customerEmail: user.email });

    return build();
  }
}

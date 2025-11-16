import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { Decimal } from '@prisma/client/runtime/library';

@Injectable()
export class FinanceService {
  constructor(private prisma: PrismaService) {}

  // Ledger operations
  async createLedger(tenantId: string, data: any) {
    const ledger = await this.prisma.ledger.create({
      data: {
        ...data,
        tenantId,
      },
    });

    // Auto-update budget if linked
    if (data.budgetId && data.type === 'EXPENSE') {
      await this.updateBudgetExpense(data.budgetId, data.amount);
    }

    return ledger;
  }

  async getLedgers(tenantId: string, projectId?: string) {
    return this.prisma.ledger.findMany({
      where: {
        tenantId,
        ...(projectId && { projectId }),
      },
      include: {
        project: { select: { id: true, name: true } },
        budget: { select: { id: true, category: true } },
      },
      orderBy: { date: 'desc' },
    });
  }

  // Budget operations
  async createBudget(tenantId: string, data: any) {
    const { budgetAmount, ...rest } = data;
    return this.prisma.financeBudget.create({
      data: {
        ...rest,
        tenantId,
        budgetAmount,
        remainingAmount: budgetAmount,
      },
    });
  }

  async getBudgets(tenantId: string, projectId?: string, year?: number) {
    return this.prisma.financeBudget.findMany({
      where: {
        tenantId,
        ...(projectId && { projectId }),
        ...(year && { year }),
      },
      include: {
        project: { select: { id: true, name: true } },
      },
      orderBy: [{ year: 'desc' }, { month: 'asc' }],
    });
  }

  async updateBudgetExpense(budgetId: string, expenseAmount: number) {
    const budget = await this.prisma.financeBudget.findUnique({
      where: { id: budgetId },
    });

    if (!budget) return;

    const newExpense = new Decimal(budget.expenseAmount).plus(expenseAmount);
    const remaining = new Decimal(budget.budgetAmount).minus(newExpense);

    return this.prisma.financeBudget.update({
      where: { id: budgetId },
      data: {
        expenseAmount: newExpense,
        remainingAmount: remaining,
      },
    });
  }

  async getCashflow(tenantId: string, projectId?: string) {
    const ledgers = await this.prisma.ledger.groupBy({
      by: ['type'],
      where: {
        tenantId,
        ...(projectId && { projectId }),
      },
      _sum: {
        amount: true,
      },
    });

    return ledgers.reduce((acc, item) => {
      acc[item.type.toLowerCase()] = item._sum.amount || 0;
      return acc;
    }, {} as Record<string, any>);
  }
}

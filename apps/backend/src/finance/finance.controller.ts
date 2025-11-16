import { Controller, Get, Post, Body, UseGuards, Query } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth } from '@nestjs/swagger';
import { FinanceService } from './finance.service';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { CurrentTenant } from '../common/decorators/current-tenant.decorator';

@ApiTags('finance')
@Controller('finance')
@UseGuards(JwtAuthGuard)
@ApiBearerAuth()
export class FinanceController {
  constructor(private readonly financeService: FinanceService) {}

  @Post('ledger')
  @ApiOperation({ summary: 'Create ledger entry' })
  createLedger(@CurrentTenant() tenantId: string, @Body() createData: any) {
    return this.financeService.createLedger(tenantId, createData);
  }

  @Get('ledger')
  @ApiOperation({ summary: 'Get ledger entries' })
  getLedgers(@CurrentTenant() tenantId: string, @Query('projectId') projectId?: string) {
    return this.financeService.getLedgers(tenantId, projectId);
  }

  @Post('budget')
  @ApiOperation({ summary: 'Create budget' })
  createBudget(@CurrentTenant() tenantId: string, @Body() createData: any) {
    return this.financeService.createBudget(tenantId, createData);
  }

  @Get('budget')
  @ApiOperation({ summary: 'Get budgets' })
  getBudgets(
    @CurrentTenant() tenantId: string,
    @Query('projectId') projectId?: string,
    @Query('year') year?: string,
  ) {
    return this.financeService.getBudgets(tenantId, projectId, year ? parseInt(year) : undefined);
  }

  @Get('cashflow')
  @ApiOperation({ summary: 'Get cashflow summary' })
  getCashflow(@CurrentTenant() tenantId: string, @Query('projectId') projectId?: string) {
    return this.financeService.getCashflow(tenantId, projectId);
  }
}

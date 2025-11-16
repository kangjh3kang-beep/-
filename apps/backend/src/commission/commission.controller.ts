import { Controller, Get, Post, Patch, Body, Param, Query, UseGuards } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth } from '@nestjs/swagger';
import { CommissionService } from './commission.service';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { CurrentTenant } from '../common/decorators/current-tenant.decorator';
import { CurrentUser } from '../common/decorators/current-user.decorator';

@ApiTags('commissions')
@Controller('commissions')
@UseGuards(JwtAuthGuard)
@ApiBearerAuth()
export class CommissionController {
  constructor(private readonly commissionService: CommissionService) {}

  @Post()
  @ApiOperation({ summary: 'Create commission' })
  create(@CurrentTenant() tenantId: string, @Body() createData: any) {
    return this.commissionService.createCommission(tenantId, createData);
  }

  @Get()
  @ApiOperation({ summary: 'Get commissions with filters' })
  getAll(
    @CurrentTenant() tenantId: string,
    @Query('userId') userId?: string,
    @Query('contractId') contractId?: string,
    @Query('agencyId') agencyId?: string,
    @Query('departmentId') departmentId?: string,
    @Query('teamId') teamId?: string,
    @Query('status') status?: string,
    @Query('type') type?: string,
  ) {
    return this.commissionService.getCommissions(tenantId, {
      userId,
      contractId,
      agencyId,
      departmentId,
      teamId,
      status,
      type,
    });
  }

  @Get('statistics')
  @ApiOperation({ summary: 'Get commission statistics' })
  getStatistics(@CurrentTenant() tenantId: string) {
    return this.commissionService.getCommissionStatistics(tenantId);
  }

  @Get('my-summary')
  @ApiOperation({ summary: 'Get current user commission summary' })
  getMySummary(@CurrentTenant() tenantId: string, @CurrentUser() user: any) {
    return this.commissionService.getUserCommissionSummary(tenantId, user.id);
  }

  @Get('users/:userId/summary')
  @ApiOperation({ summary: 'Get user commission summary' })
  getUserSummary(@CurrentTenant() tenantId: string, @Param('userId') userId: string) {
    return this.commissionService.getUserCommissionSummary(tenantId, userId);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get commission by ID' })
  getById(@Param('id') id: string, @CurrentTenant() tenantId: string) {
    return this.commissionService.getCommissionById(id, tenantId);
  }

  @Patch(':id')
  @ApiOperation({ summary: 'Update commission' })
  update(@Param('id') id: string, @Body() updateData: any) {
    return this.commissionService.updateCommission(id, updateData);
  }

  @Post(':id/approve')
  @ApiOperation({ summary: 'Approve commission' })
  approve(@Param('id') id: string, @CurrentUser() user: any) {
    return this.commissionService.approveCommission(id, user.id);
  }

  @Post(':id/pay')
  @ApiOperation({ summary: 'Mark commission as paid' })
  pay(@Param('id') id: string, @CurrentUser() user: any) {
    return this.commissionService.payCommission(id, user.id);
  }
}

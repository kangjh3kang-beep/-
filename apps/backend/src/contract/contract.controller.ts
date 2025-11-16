import { Controller, Get, Post, Body, Param, Patch, UseGuards, Query } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth } from '@nestjs/swagger';
import { ContractService } from './contract.service';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { CurrentTenant } from '../common/decorators/current-tenant.decorator';
import { CurrentUser } from '../common/decorators/current-user.decorator';

@ApiTags('contracts')
@Controller('contracts')
@UseGuards(JwtAuthGuard)
@ApiBearerAuth()
export class ContractController {
  constructor(private readonly contractService: ContractService) {}

  @Post()
  @ApiOperation({ summary: 'Create a new contract' })
  create(@CurrentTenant() tenantId: string, @CurrentUser() user: any, @Body() createData: any) {
    return this.contractService.create(tenantId, user.id, createData);
  }

  @Get()
  @ApiOperation({ summary: 'Get all contracts with filters' })
  findAll(
    @CurrentTenant() tenantId: string,
    @Query('projectId') projectId?: string,
    @Query('status') status?: string,
    @Query('salespersonId') salespersonId?: string,
    @Query('search') search?: string,
    @Query('startDate') startDate?: string,
    @Query('endDate') endDate?: string,
  ) {
    return this.contractService.findAll(tenantId, {
      projectId,
      status,
      salespersonId,
      search,
      startDate: startDate ? new Date(startDate) : undefined,
      endDate: endDate ? new Date(endDate) : undefined,
    });
  }

  @Get('statistics/summary')
  @ApiOperation({ summary: 'Get contract statistics' })
  getStatistics(@CurrentTenant() tenantId: string, @Query('projectId') projectId?: string) {
    return this.contractService.getStatistics(tenantId, projectId);
  }

  @Get('statistics/monthly')
  @ApiOperation({ summary: 'Get contracts by month' })
  getContractsByMonth(
    @CurrentTenant() tenantId: string,
    @Query('year') year?: string,
    @Query('projectId') projectId?: string,
  ) {
    const currentYear = year ? parseInt(year) : new Date().getFullYear();
    return this.contractService.getContractsByMonth(tenantId, currentYear, projectId);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get contract by ID' })
  findOne(@Param('id') id: string, @CurrentTenant() tenantId: string) {
    return this.contractService.findOne(id, tenantId);
  }

  @Patch(':id')
  @ApiOperation({ summary: 'Update contract' })
  update(@Param('id') id: string, @Body() updateData: any) {
    return this.contractService.update(id, updateData);
  }

  @Patch(':id/status')
  @ApiOperation({ summary: 'Update contract status' })
  updateStatus(@Param('id') id: string, @Body('status') status: string) {
    return this.contractService.updateStatus(id, status);
  }

  @Patch(':id/document')
  @ApiOperation({ summary: 'Upload contract document' })
  uploadDocument(@Param('id') id: string, @Body('documentUrl') documentUrl: string) {
    return this.contractService.uploadDocument(id, documentUrl);
  }

  @Post(':id/sign')
  @ApiOperation({ summary: 'Sign contract' })
  signContract(
    @Param('id') id: string,
    @Body() signData: { signedDocumentUrl: string; recordingUrl?: string },
  ) {
    return this.contractService.signContract(id, signData.signedDocumentUrl, signData.recordingUrl);
  }
}

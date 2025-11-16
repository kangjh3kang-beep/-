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
  @ApiOperation({ summary: 'Get all contracts' })
  findAll(@CurrentTenant() tenantId: string, @Query('projectId') projectId?: string) {
    return this.contractService.findAll(tenantId, projectId);
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
}

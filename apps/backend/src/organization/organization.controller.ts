import { Controller, Get, Post, Patch, Body, Param, Query, UseGuards } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth } from '@nestjs/swagger';
import { OrganizationService } from './organization.service';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { CurrentTenant } from '../common/decorators/current-tenant.decorator';

@ApiTags('organization')
@Controller('organization')
@UseGuards(JwtAuthGuard)
@ApiBearerAuth()
export class OrganizationController {
  constructor(private readonly organizationService: OrganizationService) {}

  // ============================================
  // AGENCY
  // ============================================

  @Post('agencies')
  @ApiOperation({ summary: 'Create agency' })
  createAgency(@CurrentTenant() tenantId: string, @Body() createData: any) {
    return this.organizationService.createAgency(tenantId, createData);
  }

  @Get('agencies')
  @ApiOperation({ summary: 'Get all agencies' })
  getAgencies(@CurrentTenant() tenantId: string) {
    return this.organizationService.getAgencies(tenantId);
  }

  @Get('agencies/:id')
  @ApiOperation({ summary: 'Get agency by ID' })
  getAgencyById(@Param('id') id: string, @CurrentTenant() tenantId: string) {
    return this.organizationService.getAgencyById(id, tenantId);
  }

  @Patch('agencies/:id')
  @ApiOperation({ summary: 'Update agency' })
  updateAgency(@Param('id') id: string, @Body() updateData: any) {
    return this.organizationService.updateAgency(id, updateData);
  }

  @Get('agencies/:id/statistics')
  @ApiOperation({ summary: 'Get agency statistics' })
  getAgencyStatistics(@Param('id') id: string, @CurrentTenant() tenantId: string) {
    return this.organizationService.getAgencyStatistics(tenantId, id);
  }

  // ============================================
  // DEPARTMENT
  // ============================================

  @Post('departments')
  @ApiOperation({ summary: 'Create department' })
  createDepartment(@CurrentTenant() tenantId: string, @Body() createData: any) {
    return this.organizationService.createDepartment(tenantId, createData);
  }

  @Get('departments')
  @ApiOperation({ summary: 'Get all departments' })
  getDepartments(@CurrentTenant() tenantId: string, @Query('agencyId') agencyId?: string) {
    return this.organizationService.getDepartments(tenantId, agencyId);
  }

  @Get('departments/:id')
  @ApiOperation({ summary: 'Get department by ID' })
  getDepartmentById(@Param('id') id: string, @CurrentTenant() tenantId: string) {
    return this.organizationService.getDepartmentById(id, tenantId);
  }

  @Patch('departments/:id')
  @ApiOperation({ summary: 'Update department' })
  updateDepartment(@Param('id') id: string, @Body() updateData: any) {
    return this.organizationService.updateDepartment(id, updateData);
  }

  @Get('departments/:id/statistics')
  @ApiOperation({ summary: 'Get department statistics' })
  getDepartmentStatistics(@Param('id') id: string, @CurrentTenant() tenantId: string) {
    return this.organizationService.getDepartmentStatistics(tenantId, id);
  }

  // ============================================
  // TEAM
  // ============================================

  @Post('teams')
  @ApiOperation({ summary: 'Create team' })
  createTeam(@CurrentTenant() tenantId: string, @Body() createData: any) {
    return this.organizationService.createTeam(tenantId, createData);
  }

  @Get('teams')
  @ApiOperation({ summary: 'Get all teams' })
  getTeams(@CurrentTenant() tenantId: string, @Query('departmentId') departmentId?: string) {
    return this.organizationService.getTeams(tenantId, departmentId);
  }

  @Get('teams/:id')
  @ApiOperation({ summary: 'Get team by ID' })
  getTeamById(@Param('id') id: string, @CurrentTenant() tenantId: string) {
    return this.organizationService.getTeamById(id, tenantId);
  }

  @Patch('teams/:id')
  @ApiOperation({ summary: 'Update team' })
  updateTeam(@Param('id') id: string, @Body() updateData: any) {
    return this.organizationService.updateTeam(id, updateData);
  }

  @Get('teams/:id/statistics')
  @ApiOperation({ summary: 'Get team statistics' })
  getTeamStatistics(@Param('id') id: string, @CurrentTenant() tenantId: string) {
    return this.organizationService.getTeamStatistics(tenantId, id);
  }

  @Get('users/:id/statistics')
  @ApiOperation({ summary: 'Get user contract statistics' })
  getUserStatistics(@Param('id') id: string, @CurrentTenant() tenantId: string) {
    return this.organizationService.getUserContractStats(tenantId, id);
  }
}

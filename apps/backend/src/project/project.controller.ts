import { Controller, Get, Post, Body, Param, Patch, Delete, UseGuards } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth } from '@nestjs/swagger';
import { ProjectService } from './project.service';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { CurrentTenant } from '../common/decorators/current-tenant.decorator';
import { CurrentUser } from '../common/decorators/current-user.decorator';

@ApiTags('projects')
@Controller('projects')
@UseGuards(JwtAuthGuard)
@ApiBearerAuth()
export class ProjectController {
  constructor(private readonly projectService: ProjectService) {}

  @Post()
  @ApiOperation({ summary: 'Create a new project' })
  create(@CurrentTenant() tenantId: string, @CurrentUser() user: any, @Body() createData: any) {
    return this.projectService.create(tenantId, user.id, createData);
  }

  @Get()
  @ApiOperation({ summary: 'Get all projects' })
  findAll(@CurrentTenant() tenantId: string) {
    return this.projectService.findAll(tenantId);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get project by ID' })
  findOne(@Param('id') id: string, @CurrentTenant() tenantId: string) {
    return this.projectService.findOne(id, tenantId);
  }

  @Patch(':id')
  @ApiOperation({ summary: 'Update project' })
  update(@Param('id') id: string, @CurrentTenant() tenantId: string, @Body() updateData: any) {
    return this.projectService.update(id, tenantId, updateData);
  }

  @Delete(':id')
  @ApiOperation({ summary: 'Delete project' })
  delete(@Param('id') id: string) {
    return this.projectService.delete(id);
  }
}

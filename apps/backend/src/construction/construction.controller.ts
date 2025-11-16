import { Controller, Get, Post, Body, Param, Patch, UseGuards, Query } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth } from '@nestjs/swagger';
import { ConstructionService } from './construction.service';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { CurrentTenant } from '../common/decorators/current-tenant.decorator';

@ApiTags('construction')
@Controller('construction')
@UseGuards(JwtAuthGuard)
@ApiBearerAuth()
export class ConstructionController {
  constructor(private readonly constructionService: ConstructionService) {}

  @Post()
  @ApiOperation({ summary: 'Create construction task' })
  create(@CurrentTenant() tenantId: string, @Body() createData: any) {
    return this.constructionService.create(tenantId, createData);
  }

  @Get()
  @ApiOperation({ summary: 'Get construction tasks by project' })
  findAll(@CurrentTenant() tenantId: string, @Query('projectId') projectId: string) {
    return this.constructionService.findAll(tenantId, projectId);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get construction task by ID' })
  findOne(@Param('id') id: string, @CurrentTenant() tenantId: string) {
    return this.constructionService.findOne(id, tenantId);
  }

  @Patch(':id')
  @ApiOperation({ summary: 'Update construction task' })
  update(@Param('id') id: string, @Body() updateData: any) {
    return this.constructionService.update(id, updateData);
  }

  @Patch(':id/progress')
  @ApiOperation({ summary: 'Update construction progress' })
  updateProgress(@Param('id') id: string, @Body('actualProgress') actualProgress: number) {
    return this.constructionService.updateProgress(id, actualProgress);
  }
}

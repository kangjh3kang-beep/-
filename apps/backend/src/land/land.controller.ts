import { Controller, Get, Post, Body, Param, Patch, Delete, UseGuards, Query } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth } from '@nestjs/swagger';
import { LandService } from './land.service';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { CurrentTenant } from '../common/decorators/current-tenant.decorator';

@ApiTags('land')
@Controller('land')
@UseGuards(JwtAuthGuard)
@ApiBearerAuth()
export class LandController {
  constructor(private readonly landService: LandService) {}

  @Post()
  @ApiOperation({ summary: 'Create land entry' })
  create(@CurrentTenant() tenantId: string, @Body() createData: any) {
    return this.landService.create(tenantId, createData);
  }

  @Get()
  @ApiOperation({ summary: 'Get all land entries' })
  findAll(@CurrentTenant() tenantId: string, @Query('projectId') projectId?: string) {
    return this.landService.findAll(tenantId, projectId);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get land by ID' })
  findOne(@Param('id') id: string, @CurrentTenant() tenantId: string) {
    return this.landService.findOne(id, tenantId);
  }

  @Patch(':id')
  @ApiOperation({ summary: 'Update land' })
  update(@Param('id') id: string, @Body() updateData: any) {
    return this.landService.update(id, updateData);
  }

  @Delete(':id')
  @ApiOperation({ summary: 'Delete land' })
  delete(@Param('id') id: string) {
    return this.landService.delete(id);
  }

  @Post(':id/fetch-info')
  @ApiOperation({ summary: 'Fetch land information from 토지이음 API' })
  async fetchLandInfo(@Param('id') id: string, @CurrentTenant() tenantId: string) {
    return this.landService.fetchLandInfo(id, tenantId);
  }

  @Post('bulk')
  @ApiOperation({ summary: 'Bulk create land entries with optional API data fetch' })
  async bulkCreate(
    @CurrentTenant() tenantId: string,
    @Body() data: { projectId: string; lands: any[]; fetchApiData?: boolean }
  ) {
    return this.landService.bulkCreate(tenantId, data.projectId, data.lands, data.fetchApiData);
  }
}

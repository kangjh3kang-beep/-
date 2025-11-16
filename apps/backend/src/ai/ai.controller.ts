import { Controller, Post, Body, UseGuards, Query } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth } from '@nestjs/swagger';
import { AiService } from './ai.service';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { CurrentTenant } from '../common/decorators/current-tenant.decorator';

@ApiTags('ai')
@Controller('ai')
@UseGuards(JwtAuthGuard)
@ApiBearerAuth()
export class AiController {
  constructor(private readonly aiService: AiService) {}

  @Post('recommend-salesperson')
  @ApiOperation({ summary: 'Get AI recommendation for salesperson assignment' })
  recommendSalesperson(@CurrentTenant() tenantId: string, @Body() customerData: any) {
    return this.aiService.recommendSalesperson(tenantId, customerData);
  }

  @Post('forecast-conversion')
  @ApiOperation({ summary: 'Forecast contract conversion rate' })
  forecastConversion(@CurrentTenant() tenantId: string, @Query('projectId') projectId: string) {
    return this.aiService.forecastContractConversion(tenantId, projectId);
  }

  @Post('analyze-construction')
  @ApiOperation({ summary: 'Analyze construction progress with AI' })
  analyzeConstruction(@CurrentTenant() tenantId: string, @Query('projectId') projectId: string) {
    return this.aiService.analyzeConstructionProgress(tenantId, projectId);
  }
}

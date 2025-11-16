import { Controller, Get, Post, Body, Param, UseGuards } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth } from '@nestjs/swagger';
import { InvestorService } from './investor.service';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { CurrentTenant } from '../common/decorators/current-tenant.decorator';

@ApiTags('investors')
@Controller('investors')
@UseGuards(JwtAuthGuard)
@ApiBearerAuth()
export class InvestorController {
  constructor(private readonly investorService: InvestorService) {}

  @Post()
  @ApiOperation({ summary: 'Create investor' })
  create(@CurrentTenant() tenantId: string, @Body() createData: any) {
    return this.investorService.create(tenantId, createData);
  }

  @Get()
  @ApiOperation({ summary: 'Get all investors' })
  findAll(@CurrentTenant() tenantId: string) {
    return this.investorService.findAll(tenantId);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get investor by ID' })
  findOne(@Param('id') id: string, @CurrentTenant() tenantId: string) {
    return this.investorService.findOne(id, tenantId);
  }

  @Post('nft')
  @ApiOperation({ summary: 'Create NFT' })
  createNFT(@CurrentTenant() tenantId: string, @Body() createData: any) {
    return this.investorService.createNFT(tenantId, createData);
  }

  @Get('nft/list')
  @ApiOperation({ summary: 'Get all NFTs' })
  getNFTs(@CurrentTenant() tenantId: string) {
    return this.investorService.getNFTs(tenantId);
  }
}

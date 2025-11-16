import { Controller, Get, Post, Body, Param, Query, UseGuards } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth } from '@nestjs/swagger';
import { TerminationService } from './termination.service';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { CurrentTenant } from '../common/decorators/current-tenant.decorator';
import { CurrentUser } from '../common/decorators/current-user.decorator';

@ApiTags('termination')
@Controller('termination')
@UseGuards(JwtAuthGuard)
@ApiBearerAuth()
export class TerminationController {
  constructor(private readonly terminationService: TerminationService) {}

  @Post('certificates')
  @ApiOperation({ summary: 'Issue termination certificate' })
  issueCertificate(
    @CurrentTenant() tenantId: string,
    @CurrentUser() user: any,
    @Body() data: any,
  ) {
    return this.terminationService.issueCertificate(tenantId, data.userId, user.id, data);
  }

  @Get('certificates')
  @ApiOperation({ summary: 'Get termination certificates' })
  getCertificates(@CurrentTenant() tenantId: string, @Query('userId') userId?: string) {
    return this.terminationService.getCertificates(tenantId, userId);
  }

  @Get('certificates/:id')
  @ApiOperation({ summary: 'Get certificate by ID' })
  getCertificateById(@Param('id') id: string, @CurrentTenant() tenantId: string) {
    return this.terminationService.getCertificateById(id, tenantId);
  }

  @Post('users/:id/terminate')
  @ApiOperation({ summary: 'Terminate user' })
  terminateUser(@Param('id') id: string, @Body('reason') reason: string) {
    return this.terminationService.terminateUser(id, reason);
  }
}

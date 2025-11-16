import { Controller, Get, Param, Patch, Body, UseGuards } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth } from '@nestjs/swagger';
import { UserService } from './user.service';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { CurrentTenant } from '../common/decorators/current-tenant.decorator';

@ApiTags('users')
@Controller('users')
@UseGuards(JwtAuthGuard)
@ApiBearerAuth()
export class UserController {
  constructor(private readonly userService: UserService) {}

  @Get()
  @ApiOperation({ summary: 'Get all users in tenant' })
  findAll(@CurrentTenant() tenantId: string) {
    return this.userService.findAll(tenantId);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get user by ID' })
  findOne(@Param('id') id: string, @CurrentTenant() tenantId: string) {
    return this.userService.findOne(id, tenantId);
  }

  @Patch(':id/status')
  @ApiOperation({ summary: 'Update user status' })
  updateStatus(
    @Param('id') id: string,
    @CurrentTenant() tenantId: string,
    @Body('status') status: string,
  ) {
    return this.userService.updateStatus(id, tenantId, status);
  }
}

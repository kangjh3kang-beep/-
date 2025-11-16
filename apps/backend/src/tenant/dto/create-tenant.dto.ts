import { ApiProperty } from '@nestjs/swagger';
import { IsString, IsOptional, IsEnum } from 'class-validator';

export class CreateTenantDto {
  @ApiProperty({ example: 'Acme Real Estate' })
  @IsString()
  name: string;

  @ApiProperty({ example: 'acme-real-estate' })
  @IsString()
  slug: string;

  @ApiProperty({ example: 'acme.satongpaltang.com', required: false })
  @IsOptional()
  @IsString()
  domain?: string;

  @ApiProperty({ example: 'BASIC', enum: ['BASIC', 'PRO', 'ENTERPRISE'], required: false })
  @IsOptional()
  @IsEnum(['BASIC', 'PRO', 'ENTERPRISE'])
  plan?: string;
}

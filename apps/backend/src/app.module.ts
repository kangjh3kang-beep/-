import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { ThrottlerModule } from '@nestjs/throttler';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { PrismaModule } from './prisma/prisma.module';
import { AuthModule } from './auth/auth.module';
import { TenantModule } from './tenant/tenant.module';
import { UserModule } from './user/user.module';
import { ProjectModule } from './project/project.module';
import { ContractModule } from './contract/contract.module';
import { FinanceModule } from './finance/finance.module';
import { LandModule } from './land/land.module';
import { ConstructionModule } from './construction/construction.module';
import { InvestorModule } from './investor/investor.module';
import { AiModule } from './ai/ai.module';
import { BillingModule } from './billing/billing.module';
import { UploadModule } from './upload/upload.module';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: ['.env.local', '.env'],
    }),
    ThrottlerModule.forRoot([
      {
        ttl: 60000,
        limit: 100,
      },
    ]),
    PrismaModule,
    AuthModule,
    TenantModule,
    UserModule,
    ProjectModule,
    ContractModule,
    FinanceModule,
    LandModule,
    ConstructionModule,
    InvestorModule,
    AiModule,
    BillingModule,
    UploadModule,
  ],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}

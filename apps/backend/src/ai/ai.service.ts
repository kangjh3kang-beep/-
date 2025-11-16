import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import OpenAI from 'openai';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class AiService {
  private openai: OpenAI;

  constructor(
    private configService: ConfigService,
    private prisma: PrismaService,
  ) {
    const apiKey = this.configService.get<string>('OPENAI_API_KEY');
    if (apiKey) {
      this.openai = new OpenAI({ apiKey });
    }
  }

  async recommendSalesperson(tenantId: string, customerData: any) {
    if (!this.openai) {
      throw new Error('OpenAI API key not configured');
    }

    // Get all salespeople
    const salespeople = await this.prisma.user.findMany({
      where: {
        tenantId,
        role: { level: 60 },
        status: 'ACTIVE',
      },
      include: {
        contracts: {
          where: { status: 'SIGNED' },
          select: { contractAmount: true },
        },
      },
    });

    // Use AI to recommend best salesperson
    const prompt = `Based on customer data: ${JSON.stringify(customerData)}
    And available salespeople: ${JSON.stringify(salespeople.map((s) => ({ id: s.id, name: s.name, contractCount: s.contracts.length })))}

    Recommend the best salesperson and explain why in 2-3 sentences.`;

    const response = await this.openai.chat.completions.create({
      model: 'gpt-4',
      messages: [{ role: 'user', content: prompt }],
      temperature: 0.7,
    });

    return {
      recommendation: response.choices[0].message.content,
      salespeople: salespeople.map((s) => ({
        id: s.id,
        name: s.name,
        email: s.email,
        contractCount: s.contracts.length,
      })),
    };
  }

  async forecastContractConversion(tenantId: string, projectId: string) {
    if (!this.openai) {
      throw new Error('OpenAI API key not configured');
    }

    // Get contract statistics
    const contracts = await this.prisma.contract.findMany({
      where: { tenantId, projectId },
      select: { status: true, contractAmount: true, createdAt: true },
    });

    const stats = {
      total: contracts.length,
      signed: contracts.filter((c) => c.status === 'SIGNED').length,
      pending: contracts.filter((c) => c.status === 'PENDING_SIGNATURE').length,
      draft: contracts.filter((c) => c.status === 'DRAFT').length,
    };

    const prompt = `Based on contract statistics: ${JSON.stringify(stats)}

    Predict the conversion rate for pending contracts and provide insights in JSON format:
    {
      "predictedConversionRate": <percentage>,
      "insights": "<analysis>"
    }`;

    const response = await this.openai.chat.completions.create({
      model: 'gpt-4',
      messages: [{ role: 'user', content: prompt }],
      temperature: 0.5,
      response_format: { type: 'json_object' },
    });

    return JSON.parse(response.choices[0].message.content);
  }

  async analyzeConstructionProgress(tenantId: string, projectId: string) {
    if (!this.openai) {
      throw new Error('OpenAI API key not configured');
    }

    const constructions = await this.prisma.construction.findMany({
      where: { tenantId, projectId },
      select: {
        phase: true,
        taskName: true,
        plannedProgress: true,
        actualProgress: true,
        status: true,
      },
    });

    const prompt = `Analyze construction progress data: ${JSON.stringify(constructions)}

    Identify delays, risks, and provide recommendations in JSON format:
    {
      "overallHealth": "<good|warning|critical>",
      "delayedTasks": [],
      "recommendations": []
    }`;

    const response = await this.openai.chat.completions.create({
      model: 'gpt-4',
      messages: [{ role: 'user', content: prompt }],
      temperature: 0.5,
      response_format: { type: 'json_object' },
    });

    return JSON.parse(response.choices[0].message.content);
  }
}

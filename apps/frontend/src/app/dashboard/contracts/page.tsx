'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { FileText, Search, Filter, Plus, Eye, CheckCircle, Clock, XCircle } from 'lucide-react';

interface Contract {
  id: string;
  contractNumber: string;
  customerName: string;
  customerPhone: string;
  contractAmount: number;
  status: string;
  createdAt: string;
  project: {
    id: string;
    name: string;
    code: string;
  };
  salesperson: {
    id: string;
    name: string;
  } | null;
}

const statusColors = {
  DRAFT: 'bg-gray-100 text-gray-800',
  PENDING_SIGNATURE: 'bg-yellow-100 text-yellow-800',
  SIGNED: 'bg-green-100 text-green-800',
  COMPLETED: 'bg-blue-100 text-blue-800',
  CANCELED: 'bg-red-100 text-red-800',
};

const statusIcons = {
  DRAFT: Clock,
  PENDING_SIGNATURE: Clock,
  SIGNED: CheckCircle,
  COMPLETED: CheckCircle,
  CANCELED: XCircle,
};

const statusLabels = {
  DRAFT: '초안',
  PENDING_SIGNATURE: '서명대기',
  SIGNED: '서명완료',
  COMPLETED: '완료',
  CANCELED: '취소',
};

export default function ContractsPage() {
  const router = useRouter();
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [projectFilter, setProjectFilter] = useState('');

  useEffect(() => {
    fetchContracts();
  }, [search, statusFilter, projectFilter]);

  const fetchContracts = async () => {
    try {
      const params = new URLSearchParams();
      if (search) params.append('search', search);
      if (statusFilter) params.append('status', statusFilter);
      if (projectFilter) params.append('projectId', projectFilter);

      const { data } = await api.get(`/contracts?${params.toString()}`);
      setContracts(data);
    } catch (error) {
      console.error('Failed to fetch contracts:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ko-KR');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-500">로딩 중...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">계약 관리</h1>
            <p className="text-gray-600 mt-1">모든 계약을 관리하고 추적하세요</p>
          </div>
          <Link
            href="/dashboard/contracts/new"
            className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
          >
            <Plus className="w-5 h-5 mr-2" />
            새 계약
          </Link>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="계약번호, 고객명, 전화번호 검색"
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <select
              className="px-4 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="">전체 상태</option>
              <option value="DRAFT">초안</option>
              <option value="PENDING_SIGNATURE">서명대기</option>
              <option value="SIGNED">서명완료</option>
              <option value="COMPLETED">완료</option>
              <option value="CANCELED">취소</option>
            </select>
            <button
              className="inline-flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
              onClick={() => {
                setSearch('');
                setStatusFilter('');
                setProjectFilter('');
              }}
            >
              <Filter className="w-5 h-5 mr-2" />
              필터 초기화
            </button>
          </div>
        </div>

        {/* Contracts List */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  계약번호
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  고객정보
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  현장
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  계약금액
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  담당자
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  상태
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  등록일
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  작업
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {contracts.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center text-gray-500">
                    <FileText className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                    <p>계약이 없습니다</p>
                  </td>
                </tr>
              ) : (
                contracts.map((contract) => {
                  const StatusIcon = statusIcons[contract.status as keyof typeof statusIcons];
                  return (
                    <tr key={contract.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {contract.contractNumber}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{contract.customerName}</div>
                        <div className="text-sm text-gray-500">{contract.customerPhone}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{contract.project.name}</div>
                        <div className="text-sm text-gray-500">{contract.project.code}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-semibold text-gray-900">
                          {formatCurrency(contract.contractAmount)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {contract.salesperson?.name || '-'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            statusColors[contract.status as keyof typeof statusColors]
                          }`}
                        >
                          <StatusIcon className="w-3 h-3 mr-1" />
                          {statusLabels[contract.status as keyof typeof statusLabels]}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(contract.createdAt)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <Link
                          href={`/dashboard/contracts/${contract.id}`}
                          className="text-primary-600 hover:text-primary-900 inline-flex items-center"
                        >
                          <Eye className="w-4 h-4 mr-1" />
                          보기
                        </Link>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

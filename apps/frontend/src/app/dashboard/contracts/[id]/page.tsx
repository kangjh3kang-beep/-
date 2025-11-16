'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import {
  ArrowLeft,
  FileText,
  Upload,
  Download,
  CheckCircle,
  Edit,
  Trash2,
} from 'lucide-react';

interface ContractDetail {
  id: string;
  contractNumber: string;
  customerName: string;
  customerPhone: string;
  customerEmail: string | null;
  customerAddress: string | null;
  unitNumber: string | null;
  unitType: string | null;
  unitArea: number | null;
  contractAmount: number;
  downPayment: number | null;
  middlePayment: number | null;
  finalPayment: number | null;
  commissionRate: number | null;
  commissionAmount: number | null;
  commissionPaid: boolean;
  status: string;
  documentUrl: string | null;
  signedDocumentUrl: string | null;
  recordingUrl: string | null;
  signedAt: string | null;
  contractDate: string | null;
  createdAt: string;
  updatedAt: string;
  project: {
    id: string;
    name: string;
    code: string;
    address: string;
  };
  salesperson: {
    id: string;
    name: string;
    email: string;
  } | null;
  createdBy: {
    id: string;
    name: string;
    email: string;
  };
}

export default function ContractDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [contract, setContract] = useState<ContractDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    fetchContract();
  }, [params.id]);

  const fetchContract = async () => {
    try {
      const { data } = await api.get(`/contracts/${params.id}`);
      setContract(data);
    } catch (error) {
      console.error('Failed to fetch contract:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (file: File, type: 'document' | 'signed' | 'recording') => {
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const { data } = await api.post('/upload/file?folder=contracts', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      if (type === 'document') {
        await api.patch(`/contracts/${params.id}/document`, { documentUrl: data.url });
      } else if (type === 'signed') {
        await api.post(`/contracts/${params.id}/sign`, { signedDocumentUrl: data.url });
      }

      await fetchContract();
      alert('파일이 업로드되었습니다.');
    } catch (error) {
      console.error('Failed to upload file:', error);
      alert('파일 업로드에 실패했습니다.');
    } finally {
      setUploading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  if (loading || !contract) {
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
        <div className="mb-8">
          <Link
            href="/dashboard/contracts"
            className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            계약 목록으로
          </Link>
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{contract.contractNumber}</h1>
              <p className="text-gray-600 mt-1">{contract.customerName}</p>
            </div>
            <div className="flex space-x-3">
              <Link
                href={`/dashboard/contracts/${contract.id}/edit`}
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                <Edit className="w-5 h-5 mr-2" />
                수정
              </Link>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Customer Info */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">고객 정보</h2>
              <dl className="grid grid-cols-2 gap-4">
                <div>
                  <dt className="text-sm text-gray-500">이름</dt>
                  <dd className="mt-1 text-sm font-medium text-gray-900">{contract.customerName}</dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-500">연락처</dt>
                  <dd className="mt-1 text-sm font-medium text-gray-900">{contract.customerPhone}</dd>
                </div>
                {contract.customerEmail && (
                  <div>
                    <dt className="text-sm text-gray-500">이메일</dt>
                    <dd className="mt-1 text-sm font-medium text-gray-900">
                      {contract.customerEmail}
                    </dd>
                  </div>
                )}
                {contract.customerAddress && (
                  <div className="col-span-2">
                    <dt className="text-sm text-gray-500">주소</dt>
                    <dd className="mt-1 text-sm font-medium text-gray-900">
                      {contract.customerAddress}
                    </dd>
                  </div>
                )}
              </dl>
            </div>

            {/* Unit Info */}
            {contract.unitNumber && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold mb-4">분양 정보</h2>
                <dl className="grid grid-cols-3 gap-4">
                  <div>
                    <dt className="text-sm text-gray-500">호수</dt>
                    <dd className="mt-1 text-sm font-medium text-gray-900">{contract.unitNumber}</dd>
                  </div>
                  {contract.unitType && (
                    <div>
                      <dt className="text-sm text-gray-500">타입</dt>
                      <dd className="mt-1 text-sm font-medium text-gray-900">{contract.unitType}</dd>
                    </div>
                  )}
                  {contract.unitArea && (
                    <div>
                      <dt className="text-sm text-gray-500">면적</dt>
                      <dd className="mt-1 text-sm font-medium text-gray-900">
                        {contract.unitArea}㎡
                      </dd>
                    </div>
                  )}
                </dl>
              </div>
            )}

            {/* Financial Info */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">금액 정보</h2>
              <dl className="space-y-3">
                <div className="flex justify-between items-center border-b pb-3">
                  <dt className="text-sm text-gray-500">총 계약금액</dt>
                  <dd className="text-lg font-bold text-gray-900">
                    {formatCurrency(contract.contractAmount)}
                  </dd>
                </div>
                {contract.downPayment && (
                  <div className="flex justify-between items-center">
                    <dt className="text-sm text-gray-500">계약금</dt>
                    <dd className="text-sm font-medium text-gray-900">
                      {formatCurrency(contract.downPayment)}
                    </dd>
                  </div>
                )}
                {contract.middlePayment && (
                  <div className="flex justify-between items-center">
                    <dt className="text-sm text-gray-500">중도금</dt>
                    <dd className="text-sm font-medium text-gray-900">
                      {formatCurrency(contract.middlePayment)}
                    </dd>
                  </div>
                )}
                {contract.finalPayment && (
                  <div className="flex justify-between items-center">
                    <dt className="text-sm text-gray-500">잔금</dt>
                    <dd className="text-sm font-medium text-gray-900">
                      {formatCurrency(contract.finalPayment)}
                    </dd>
                  </div>
                )}
              </dl>
            </div>

            {/* Documents */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">계약 문서</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    계약서
                  </label>
                  {contract.documentUrl ? (
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                      <div className="flex items-center">
                        <FileText className="w-5 h-5 text-gray-400 mr-2" />
                        <span className="text-sm text-gray-900">계약서.pdf</span>
                      </div>
                      <a
                        href={contract.documentUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary-600 hover:text-primary-700"
                      >
                        <Download className="w-5 h-5" />
                      </a>
                    </div>
                  ) : (
                    <label className="flex items-center justify-center w-full h-32 px-4 transition bg-white border-2 border-gray-300 border-dashed rounded-md appearance-none cursor-pointer hover:border-gray-400 focus:outline-none">
                      <span className="flex items-center space-x-2">
                        <Upload className="w-6 h-6 text-gray-600" />
                        <span className="font-medium text-gray-600">
                          {uploading ? '업로드 중...' : '파일 업로드'}
                        </span>
                      </span>
                      <input
                        type="file"
                        className="hidden"
                        accept=".pdf,.doc,.docx"
                        onChange={(e) =>
                          e.target.files?.[0] && handleFileUpload(e.target.files[0], 'document')
                        }
                        disabled={uploading}
                      />
                    </label>
                  )}
                </div>

                {contract.signedDocumentUrl && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      서명된 계약서
                    </label>
                    <div className="flex items-center justify-between p-3 bg-green-50 rounded-md">
                      <div className="flex items-center">
                        <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
                        <span className="text-sm text-gray-900">서명완료_계약서.pdf</span>
                      </div>
                      <a
                        href={contract.signedDocumentUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary-600 hover:text-primary-700"
                      >
                        <Download className="w-5 h-5" />
                      </a>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Status */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">계약 상태</h2>
              <div className="space-y-3">
                <div>
                  <dt className="text-sm text-gray-500">상태</dt>
                  <dd className="mt-1">
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                      {contract.status}
                    </span>
                  </dd>
                </div>
                {contract.signedAt && (
                  <div>
                    <dt className="text-sm text-gray-500">서명일시</dt>
                    <dd className="mt-1 text-sm font-medium text-gray-900">
                      {formatDate(contract.signedAt)}
                    </dd>
                  </div>
                )}
              </div>
            </div>

            {/* Project Info */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">현장 정보</h2>
              <div className="space-y-3">
                <div>
                  <dt className="text-sm text-gray-500">현장명</dt>
                  <dd className="mt-1 text-sm font-medium text-gray-900">{contract.project.name}</dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-500">현장코드</dt>
                  <dd className="mt-1 text-sm font-medium text-gray-900">{contract.project.code}</dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-500">주소</dt>
                  <dd className="mt-1 text-sm text-gray-900">{contract.project.address}</dd>
                </div>
              </div>
            </div>

            {/* Salesperson Info */}
            {contract.salesperson && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold mb-4">담당 상담사</h2>
                <div className="space-y-3">
                  <div>
                    <dt className="text-sm text-gray-500">이름</dt>
                    <dd className="mt-1 text-sm font-medium text-gray-900">
                      {contract.salesperson.name}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm text-gray-500">이메일</dt>
                    <dd className="mt-1 text-sm text-gray-900">{contract.salesperson.email}</dd>
                  </div>
                </div>
              </div>
            )}

            {/* Commission Info */}
            {contract.commissionAmount && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold mb-4">수수료 정보</h2>
                <div className="space-y-3">
                  <div>
                    <dt className="text-sm text-gray-500">수수료율</dt>
                    <dd className="mt-1 text-sm font-medium text-gray-900">
                      {contract.commissionRate}%
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm text-gray-500">수수료 금액</dt>
                    <dd className="mt-1 text-sm font-medium text-gray-900">
                      {formatCurrency(contract.commissionAmount)}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm text-gray-500">지급 상태</dt>
                    <dd className="mt-1">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          contract.commissionPaid
                            ? 'bg-green-100 text-green-800'
                            : 'bg-yellow-100 text-yellow-800'
                        }`}
                      >
                        {contract.commissionPaid ? '지급완료' : '미지급'}
                      </span>
                    </dd>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

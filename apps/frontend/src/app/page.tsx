import Link from 'next/link';
import { Building2, TrendingUp, Users, FileText } from 'lucide-react';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-primary-600">사통팔땅</h1>
            <div className="space-x-4">
              <Link
                href="/login"
                className="text-gray-600 hover:text-gray-900"
              >
                로그인
              </Link>
              <Link
                href="/register"
                className="bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700"
              >
                시작하기
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-16">
          <h2 className="text-5xl font-bold text-gray-900 mb-4">
            부동산 개발사업 통합관리 플랫폼
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            현장·계약·회계·공정을 하나의 클라우드에서 관리하세요
          </p>
          <Link
            href="/register"
            className="inline-block bg-primary-600 text-white px-8 py-3 rounded-lg text-lg font-semibold hover:bg-primary-700"
          >
            무료로 시작하기
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mt-16">
          <FeatureCard
            icon={<Building2 className="w-8 h-8" />}
            title="현장 관리"
            description="모든 개발 현장을 중앙에서 통합 관리"
          />
          <FeatureCard
            icon={<FileText className="w-8 h-8" />}
            title="계약 관리"
            description="전자서명, 녹취, 녹화 지원"
          />
          <FeatureCard
            icon={<TrendingUp className="w-8 h-8" />}
            title="수지 관리"
            description="실시간 회계 및 수지표 자동 동기화"
          />
          <FeatureCard
            icon={<Users className="w-8 h-8" />}
            title="리츠 관리"
            description="NFT 분양권 및 투자자 관리"
          />
        </div>
      </main>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="bg-white p-6 rounded-lg shadow-md hover:shadow-xl transition-shadow">
      <div className="text-primary-600 mb-4">{icon}</div>
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  );
}

import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Shield, Settings, FileText, Plus, Menu, X } from 'lucide-react';
import { OfficeConfig } from '@/components/Config/OfficeConfig';
import { ReportStatus } from '@/components/Report/ReportStatus';
import { ReportSubmissionForm } from '@/components/Report/ReportSubmissionForm';
import { ReportsList } from '@/components/Report/ReportsList';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <main className="container mx-auto px-4 py-8 max-w-6xl">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/submit" element={<ReportSubmissionForm />} />
            <Route path="/reports" element={<ReportsList />} />
            <Route path="/reports/:id" element={<ReportDetailPage />} />
            <Route path="/config" element={<OfficeConfig />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

function Navigation() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Home', icon: Shield },
    { path: '/submit', label: 'Submit Report', icon: Plus },
    { path: '/reports', label: 'Reports', icon: FileText },
    { path: '/config', label: 'Configuration', icon: Settings },
  ];

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="container mx-auto px-4 max-w-6xl">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <Shield className="w-8 h-8 text-primary-600" />
            <span className="text-xl font-bold text-gray-900">Violation Reporter</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center px-4 py-2 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                >
                  <Icon className="w-4 h-4 mr-2" />
                  {item.label}
                </Link>
              );
            })}
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="md:hidden p-2 text-gray-600 hover:text-gray-900"
          >
            {isMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <div className="md:hidden py-4 border-t">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setIsMenuOpen(false)}
                  className={`flex items-center px-4 py-3 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <Icon className="w-5 h-5 mr-3" />
                  {item.label}
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </nav>
  );
}

function HomePage() {
  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="text-center py-12 bg-gradient-to-br from-primary-600 to-primary-700 rounded-2xl text-white">
        <Shield className="w-16 h-16 mx-auto mb-4" />
        <h1 className="text-4xl font-bold mb-4">Public Interest Violation Reporter</h1>
        <p className="text-lg text-primary-100 max-w-2xl mx-auto">
          Report public interest violations using AI-powered image and video analysis.
          Our system automatically detects harmful content and files complaints with relevant authorities.
        </p>
        <div className="mt-8 flex justify-center space-x-4">
          <Link
            to="/submit"
            className="px-6 py-3 bg-white text-primary-700 font-semibold rounded-lg hover:bg-gray-100 transition-colors"
          >
            Submit a Report
          </Link>
          <Link
            to="/reports"
            className="px-6 py-3 bg-primary-500 text-white font-semibold rounded-lg hover:bg-primary-400 transition-colors"
          >
            View Reports
          </Link>
        </div>
      </div>

      {/* Features Section */}
      <div className="grid md:grid-cols-3 gap-6">
        <FeatureCard
          icon={Shield}
          title="AI-Powered Analysis"
          description="Advanced vision-language model analyzes images and videos to detect violations and extract location data."
        />
        <FeatureCard
          icon={FileText}
          title="Automated Reporting"
          description="Valid reports are automatically submitted to configured authorities via hotline or web service."
        />
        <FeatureCard
          icon={Settings}
          title="Configurable"
          description="Easily configure multiple offices and endpoints to handle different types of violations."
        />
      </div>

      {/* How It Works */}
      <div className="bg-white rounded-xl p-8 shadow-sm">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">How It Works</h2>
        <div className="grid md:grid-cols-4 gap-6">
          <StepCard
            number={1}
            title="Upload Media"
            description="Upload images, videos, or audio of the violation you want to report."
          />
          <StepCard
            number={2}
            title="AI Analysis"
            description="Our AI analyzes the content to detect violations and extract location information."
          />
          <StepCard
            number={3}
            title="Review"
            description="The system automatically approves clear cases or flags uncertain ones for review."
          />
          <StepCard
            number={4}
            title="Auto-Submit"
            description="Approved reports are automatically filed with the appropriate authorities."
          />
        </div>
      </div>
    </div>
  );
}

function FeatureCard({ icon: Icon, title, description }: { icon: React.ElementType; title: string; description: string }) {
  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
      <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4">
        <Icon className="w-6 h-6 text-primary-600" />
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  );
}

function StepCard({ number, title, description }: { number: number; title: string; description: string }) {
  return (
    <div className="text-center">
      <div className="w-10 h-10 bg-primary-600 text-white rounded-full flex items-center justify-center mx-auto mb-3 font-bold">
        {number}
      </div>
      <h3 className="font-semibold text-gray-900 mb-1">{title}</h3>
      <p className="text-sm text-gray-600">{description}</p>
    </div>
  );
}

function ReportDetailPage() {
  const location = useLocation();
  const reportId = parseInt(location.pathname.split('/').pop() || '0');

  if (!reportId) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Invalid report ID</p>
      </div>
    );
  }

  return (
    <div>
      <Link
        to="/reports"
        className="text-sm text-primary-600 hover:text-primary-700 mb-4 inline-block"
      >
        ← Back to Reports
      </Link>
      <ReportStatus reportId={reportId} />
    </div>
  );
}

export default App;

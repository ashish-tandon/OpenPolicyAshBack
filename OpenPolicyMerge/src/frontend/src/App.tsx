/**
 * OpenPolicy Merge - Main React Application
 * 
 * Modern React frontend that integrates with the unified OpenPolicy Merge API.
 * Features comprehensive Canadian civic data browsing, search, and monitoring.
 */

import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from '@/components/ui/toaster';

// Layout components
import { Navigation } from '@/components/layout/Navigation';
import { Footer } from '@/components/layout/Footer';
import { ErrorBoundary } from '@/components/ErrorBoundary';

// Page components
import { HomePage } from '@/pages/HomePage';
import { JurisdictionsPage } from '@/pages/JurisdictionsPage';
import { JurisdictionDetailPage } from '@/pages/JurisdictionDetailPage';
import { RepresentativesPage } from '@/pages/RepresentativesPage';
import { RepresentativeDetailPage } from '@/pages/RepresentativeDetailPage';
import { BillsPage } from '@/pages/BillsPage';
import { BillDetailPage } from '@/pages/BillDetailPage';
import { SearchPage } from '@/pages/SearchPage';
import { MonitoringPage } from '@/pages/MonitoringPage';
import { APIDocsPage } from '@/pages/APIDocsPage';
import { AboutPage } from '@/pages/AboutPage';
import { NotFoundPage } from '@/pages/NotFoundPage';

// Global styles
import './index.css';

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 2,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <ErrorBoundary>
          <div className="min-h-screen bg-gray-50 flex flex-col">
            {/* Header Navigation */}
            <Navigation />
            
            {/* Main Content */}
            <main className="flex-1">
              <Routes>
                {/* Home */}
                <Route path="/" element={<HomePage />} />
                
                {/* Jurisdictions */}
                <Route path="/jurisdictions" element={<JurisdictionsPage />} />
                <Route path="/jurisdictions/:id" element={<JurisdictionDetailPage />} />
                
                {/* Representatives */}
                <Route path="/representatives" element={<RepresentativesPage />} />
                <Route path="/representatives/:id" element={<RepresentativeDetailPage />} />
                
                {/* Bills */}
                <Route path="/bills" element={<BillsPage />} />
                <Route path="/bills/:id" element={<BillDetailPage />} />
                
                {/* Search */}
                <Route path="/search" element={<SearchPage />} />
                
                {/* Monitoring & Admin */}
                <Route path="/monitoring" element={<MonitoringPage />} />
                
                {/* Documentation */}
                <Route path="/api-docs" element={<APIDocsPage />} />
                <Route path="/about" element={<AboutPage />} />
                
                {/* 404 */}
                <Route path="*" element={<NotFoundPage />} />
              </Routes>
            </main>
            
            {/* Footer */}
            <Footer />
          </div>
          
          {/* Toast notifications */}
          <Toaster />
        </ErrorBoundary>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
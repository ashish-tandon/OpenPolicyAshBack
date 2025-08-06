/**
 * OpenPolicy Merge - Homepage Component
 * 
 * Landing page showcasing the platform's capabilities with real-time statistics,
 * featured content, and comprehensive search functionality.
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { 
  Users, 
  Building2, 
  FileText, 
  TrendingUp, 
  Search,
  MapPin,
  Calendar,
  Shield,
  Zap,
  BarChart3
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { apiClient } from '@/lib/api-client';
import { formatNumber, formatDate } from '@/lib/utils';

interface SystemStats {
  jurisdictions: number;
  representatives: number;
  bills: number;
  events: number;
  committees: number;
  votes: number;
  data_freshness: {
    recent_scrapes_24h: number;
    last_successful_scrape: string | null;
    data_age_hours: number | null;
  };
}

export function HomePage() {
  // Fetch system statistics
  const { data: stats, isLoading: statsLoading } = useQuery<SystemStats>({
    queryKey: ['system-stats'],
    queryFn: () => apiClient.get('/stats').then(res => res.data),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const [searchQuery, setSearchQuery] = React.useState('');

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      window.location.href = `/search?q=${encodeURIComponent(searchQuery.trim())}`;
    }
  };

  const features = [
    {
      icon: Building2,
      title: 'All Jurisdictions',
      description: 'Federal, provincial, territorial, and municipal governments across Canada',
      stats: stats?.jurisdictions || 0,
      href: '/jurisdictions'
    },
    {
      icon: Users,
      title: 'Representatives',
      description: 'MPs, MLAs, mayors, councillors, and other elected officials',
      stats: stats?.representatives || 0,
      href: '/representatives'
    },
    {
      icon: FileText,
      title: 'Bills & Legislation',
      description: 'Current and historical bills, acts, and legislative documents',
      stats: stats?.bills || 0,
      href: '/bills'
    },
    {
      icon: Calendar,
      title: 'Events & Meetings',
      description: 'Committee meetings, debates, and other political events',
      stats: stats?.events || 0,
      href: '/events'
    }
  ];

  const highlights = [
    {
      icon: Zap,
      title: 'Real-time Updates',
      description: 'Daily scraping ensures the most current political information'
    },
    {
      icon: Shield,
      title: 'Data Quality',
      description: 'Cross-validation and audit trails ensure accuracy and reliability'
    },
    {
      icon: Search,
      title: 'Advanced Search',
      description: 'Full-text search across all entities with intelligent filtering'
    },
    {
      icon: BarChart3,
      title: 'Monitoring',
      description: 'Comprehensive monitoring and performance metrics'
    }
  ];

  return (
    <div className="space-y-16">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900 text-white">
        <div className="absolute inset-0 bg-black/20"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <div className="text-center max-w-4xl mx-auto">
            <h1 className="text-4xl md:text-6xl font-bold mb-6">
              Canadian Civic Data
              <span className="block text-blue-300">Unified & Accessible</span>
            </h1>
            <p className="text-xl md:text-2xl mb-8 text-blue-100">
              Comprehensive platform bringing together federal, provincial, and municipal 
              political information through modern APIs and intuitive interfaces.
            </p>
            
            {/* Search Bar */}
            <form onSubmit={handleSearch} className="max-w-2xl mx-auto mb-8">
              <div className="flex gap-2">
                <Input
                  type="text"
                  placeholder="Search representatives, bills, jurisdictions..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="flex-1 h-12 text-lg bg-white/10 border-white/20 text-white placeholder:text-blue-200"
                />
                <Button type="submit" size="lg" className="bg-blue-600 hover:bg-blue-700">
                  <Search className="h-5 w-5" />
                </Button>
              </div>
            </form>
            
            {/* Quick Stats */}
            {statsLoading ? (
              <div className="flex justify-center">
                <LoadingSpinner className="h-8 w-8" />
              </div>
            ) : stats && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                <div>
                  <div className="text-2xl md:text-3xl font-bold text-blue-300">
                    {formatNumber(stats.jurisdictions)}
                  </div>
                  <div className="text-sm text-blue-200">Jurisdictions</div>
                </div>
                <div>
                  <div className="text-2xl md:text-3xl font-bold text-blue-300">
                    {formatNumber(stats.representatives)}
                  </div>
                  <div className="text-sm text-blue-200">Representatives</div>
                </div>
                <div>
                  <div className="text-2xl md:text-3xl font-bold text-blue-300">
                    {formatNumber(stats.bills)}
                  </div>
                  <div className="text-sm text-blue-200">Bills</div>
                </div>
                <div>
                  <div className="text-2xl md:text-3xl font-bold text-blue-300">
                    {stats.data_freshness.recent_scrapes_24h}
                  </div>
                  <div className="text-sm text-blue-200">Updates Today</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Features Grid */}
        <section className="space-y-8">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Comprehensive Canadian Political Data
            </h2>
            <p className="text-lg text-gray-600 max-w-3xl mx-auto">
              Access detailed information about all levels of Canadian government, 
              from federal Parliament to municipal councils.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature) => {
              const Icon = feature.icon;
              return (
                <Card key={feature.title} className="group hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <Icon className="h-8 w-8 text-blue-600" />
                      <Badge variant="secondary" className="text-lg font-semibold">
                        {formatNumber(feature.stats)}
                      </Badge>
                    </div>
                    <CardTitle className="group-hover:text-blue-600 transition-colors">
                      {feature.title}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <CardDescription className="mb-4">
                      {feature.description}
                    </CardDescription>
                    <Button asChild variant="outline" className="w-full">
                      <Link to={feature.href}>Explore</Link>
                    </Button>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </section>

        {/* Platform Highlights */}
        <section className="space-y-8">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Why OpenPolicy Merge?
            </h2>
            <p className="text-lg text-gray-600">
              Modern technology meets democratic transparency
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {highlights.map((highlight) => {
              const Icon = highlight.icon;
              return (
                <div key={highlight.title} className="flex items-start space-x-4">
                  <div className="flex-shrink-0">
                    <div className="h-12 w-12 bg-blue-100 rounded-lg flex items-center justify-center">
                      <Icon className="h-6 w-6 text-blue-600" />
                    </div>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      {highlight.title}
                    </h3>
                    <p className="text-gray-600">
                      {highlight.description}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* Data Freshness */}
        {stats && (
          <section className="bg-green-50 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-green-900 mb-2">
                  Data Freshness
                </h3>
                <p className="text-green-700">
                  {stats.data_freshness.last_successful_scrape ? (
                    <>
                      Last updated: {formatDate(stats.data_freshness.last_successful_scrape)}
                      {stats.data_freshness.data_age_hours && stats.data_freshness.data_age_hours < 24 && (
                        <Badge variant="secondary" className="ml-2 bg-green-100 text-green-800">
                          Fresh
                        </Badge>
                      )}
                    </>
                  ) : (
                    'Initializing data collection...'
                  )}
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-green-600" />
            </div>
          </section>
        )}

        {/* API Access */}
        <section className="bg-gray-100 rounded-lg p-8 text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Developers & Researchers
          </h2>
          <p className="text-gray-600 mb-6">
            Access all data through our comprehensive REST and GraphQL APIs. 
            Complete with Swagger documentation and examples.
          </p>
          <div className="flex justify-center space-x-4">
            <Button asChild>
              <Link to="/api-docs">API Documentation</Link>
            </Button>
            <Button asChild variant="outline">
              <Link to="/monitoring">System Status</Link>
            </Button>
          </div>
        </section>

        {/* Quick Actions */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <MapPin className="h-5 w-5 mr-2 text-blue-600" />
                Find Your Representative
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600 mb-4">
                Search by postal code, address, or jurisdiction to find your elected officials.
              </p>
              <Button asChild className="w-full">
                <Link to="/representatives">Search Now</Link>
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <FileText className="h-5 w-5 mr-2 text-green-600" />
                Track Legislation
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600 mb-4">
                Follow bills through the legislative process from introduction to royal assent.
              </p>
              <Button asChild className="w-full">
                <Link to="/bills">Browse Bills</Link>
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Building2 className="h-5 w-5 mr-2 text-purple-600" />
                Explore Jurisdictions
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600 mb-4">
                Discover information about federal, provincial, and municipal governments.
              </p>
              <Button asChild className="w-full">
                <Link to="/jurisdictions">View All</Link>
              </Button>
            </CardContent>
          </Card>
        </section>
      </div>
    </div>
  );
}
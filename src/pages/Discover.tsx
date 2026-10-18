import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { useNavigate } from 'react-router-dom';
import { 
  Compass, 
  Search, 
  Check, 
  Plus, 
  Play, 
  Building2, 
  AlertCircle, 
  ExternalLink,
  Database,
  Eye,
  AlertTriangle,
  MapPin,
  Phone,
  Mail,
  Info,
  X
} from 'lucide-react';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { 
  DiscoveryResultItem, 
  ProviderConfigStatus, 
  DiscoveryRunRecord 
} from '../types';

export const Discover: React.FC = () => {
  const { addToast, setSelectedProspectId, runAudit, refreshProspects } = useApp();
  const navigate = useNavigate();

  // Search parameters
  const [providerId, setProviderId] = useState<string>('osm');
  const [category, setCategory] = useState('restaurant');
  const [country, setCountry] = useState('India');
  const [region, setRegion] = useState('Maharashtra');
  const [city, setCity] = useState('Navi Mumbai');
  const [conditionFilter, setConditionFilter] = useState<string>('all');
  const [maxResults, setMaxResults] = useState('25');

  // Providers & Categories from Backend
  const [providers, setProviders] = useState<ProviderConfigStatus[]>([]);
  const [supportedCategories, setSupportedCategories] = useState<{ category: string; label: string; notes?: string }[]>([]);
  const [unmappedGuidance, setUnmappedGuidance] = useState<string>('');

  // Discovery execution state
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [results, setResults] = useState<DiscoveryResultItem[]>([]);
  const [searchDurationMs, setSearchDurationMs] = useState<number | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [searchWarnings, setSearchWarnings] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState<'all' | 'not_listed' | 'with_website' | 'saved' | 'not_saved'>('all');

  // Inspect detail modal
  const [inspectItem, setInspectItem] = useState<DiscoveryResultItem | null>(null);
  const [isSavingId, setIsSavingId] = useState<string | null>(null);

  // Fetch providers and category metadata on mount
  useEffect(() => {
    fetch('/api/discovery/providers')
      .then((res) => (res.ok ? res.json() : []))
      .then((data: ProviderConfigStatus[]) => {
        setProviders(data);
      })
      .catch(() => {});

    fetch('/api/discovery/categories')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data && data.categories) {
          setSupportedCategories(data.categories);
          setUnmappedGuidance(data.unmapped_guidance || '');
        }
      })
      .catch(() => {});
  }, []);

  const currentProvider = providers.find((p) => p.provider_id === providerId);

  const handleSearch = async () => {
    if (!category.trim()) {
      addToast('Please enter or select a business category.', 'warning');
      return;
    }
    if (!city.trim() && !region.trim()) {
      addToast('Please specify a city or region for bounded geographic search.', 'warning');
      return;
    }

    if (currentProvider && !currentProvider.is_configured) {
      addToast(`Provider '${currentProvider.name}' is not configured: ${currentProvider.status_message}`, 'error');
      setSearchError(`${currentProvider.name} is not configured: ${currentProvider.status_message}`);
      return;
    }

    setIsSearching(true);
    setSearchError(null);
    setSearchWarnings([]);
    const startTime = performance.now();

    try {
      const response = await fetch('/api/discovery/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: providerId,
          category: category.trim(),
          country: country.trim(),
          region: region.trim() || undefined,
          city: city.trim() || undefined,
          limit: parseInt(maxResults, 10) || 25,
          condition_filter: conditionFilter
        })
      });

      const elapsed = Math.round(performance.now() - startTime);
      setSearchDurationMs(elapsed);

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Search failed with status ${response.status}`);
      }

      const runRecord: DiscoveryRunRecord = await response.json();
      setHasSearched(true);

      if (runRecord.status === 'FAILED') {
        throw new Error(runRecord.error_message || 'Search execution failed on provider.');
      }

      setResults(runRecord.results || []);
      setSearchWarnings(runRecord.warnings || []);

      if (runRecord.results && runRecord.results.length > 0) {
        addToast(`Found ${runRecord.results.length} genuine business records from ${currentProvider?.name || 'provider'}`, 'success');
      } else {
        addToast(`0 records found for "${category}" in ${city} via ${currentProvider?.name || 'provider'}`, 'info');
      }
    } catch (err: any) {
      setHasSearched(true);
      setSearchError(err.message || 'An error occurred contacting the discovery provider.');
      setResults([]);
      addToast(`Discovery search failed: ${err.message}`, 'error');
    } finally {
      setIsSearching(false);
    }
  };

  const handleSaveProspect = async (item: DiscoveryResultItem) => {
    setIsSavingId(item.id);
    try {
      const response = await fetch('/api/discovery/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(item)
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Failed to save prospect (${response.status})`);
      }

      const savedData = await response.json();
      await refreshProspects();

      // Update local state to show saved
      setResults((prev) =>
        prev.map((r) =>
          r.id === item.id
            ? { ...r, is_saved: true, matched_existing_id: savedData.id }
            : r
        )
      );

      if (inspectItem && inspectItem.id === item.id) {
        setInspectItem({ ...inspectItem, is_saved: true, matched_existing_id: savedData.id });
      }

      addToast(`"${item.name}" saved to your prospect pipeline.`, 'success');
    } catch (err: any) {
      addToast(`Failed to save prospect: ${err.message}`, 'error');
    } finally {
      setIsSavingId(null);
    }
  };

  const handleOpenProspect = (prospectId: string) => {
    setSelectedProspectId(prospectId);
    navigate('/prospects');
  };

  const handleRunAuditForDiscovered = async (item: DiscoveryResultItem) => {
    if (!item.website_url) {
      addToast('Cannot audit: Business has no listed website URL.', 'warning');
      return;
    }

    try {
      // If not yet saved, save it first so audit report can link to it
      let targetId = item.matched_existing_id;
      if (!targetId) {
        const response = await fetch('/api/discovery/save', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(item)
        });
        if (response.ok) {
          const savedData = await response.json();
          targetId = savedData.id;
          await refreshProspects();
        }
      }

      if (targetId) {
        setSelectedProspectId(targetId);
        addToast(`Running live website audit for ${item.name}...`, 'info');
        await runAudit(targetId);
        navigate('/audits');
      }
    } catch (err: any) {
      addToast(`Audit error: ${err.message}`, 'error');
    }
  };

  // Filtered view
  const visibleResults = results.filter((item) => {
    if (activeTab === 'not_listed') return !item.website_url;
    if (activeTab === 'with_website') return !!item.website_url;
    if (activeTab === 'saved') return item.is_saved;
    if (activeTab === 'not_saved') return !item.is_saved;
    return true;
  });

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-[#111214]">
      {/* Page Header */}
      <div className="px-6 pt-5 pb-3 border-b border-[#22252A] flex flex-col gap-3 shrink-0">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-[24px] font-semibold text-[#F3F4F6] tracking-tight">
              Real business discovery
            </h1>
            <p className="text-[12px] text-[#A0A5AD] mt-0.5">
              Query live geographic registries and web indices for commercial entities without synthetic claims.
            </p>
          </div>

          {/* Provider status badge */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded bg-[#17191C] border border-[#2B2F36] text-[12px]">
            <Database className="w-3.5 h-3.5 text-[#D8E7A2]" />
            <span className="text-[#A0A5AD]">Active Provider:</span>
            <span className="text-[#F3F4F6] font-medium">
              {currentProvider?.name || 'OpenStreetMap (Overpass)'}
            </span>
            <span
              className={`font-mono text-[11px] px-1.5 py-0.5 rounded border ${
                currentProvider?.is_configured
                  ? 'text-[#80B89A] bg-[#18261F] border-[#253E31]'
                  : 'text-[#D78383] bg-[#2A1818] border-[#4A2626]'
              }`}
            >
              {currentProvider?.is_configured ? 'Live API' : 'Not Configured'}
            </span>
          </div>
        </div>
      </div>

      {/* Main Container */}
      <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-5">
        {/* Search Parameter Card */}
        <div className="rounded border border-[#2B2F36] bg-[#17191C] p-4 flex flex-col gap-3.5">
          <div className="flex items-center justify-between border-b border-[#22252B] pb-2">
            <span className="text-[12px] font-medium text-[#F3F4F6] flex items-center gap-2">
              <Compass className="w-3.5 h-3.5 text-[#D8E7A2]" /> Provider & Geographic Parameters
            </span>
            <span className="text-[11px] text-[#727780]">
              Deterministic live querying · Real provider records only
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-4 xl:grid-cols-8 gap-3">
            {/* Provider Selector */}
            <div>
              <label className="block text-[11px] font-medium text-[#A0A5AD] mb-1">Provider</label>
              <select
                value={providerId}
                onChange={(e) => setProviderId(e.target.value)}
                className="w-full bg-[#111214] border border-[#30343A] rounded px-2.5 py-1.5 text-[12px] text-[#F3F4F6] focus:border-[#4B5361] outline-none"
              >
                <option value="osm">OpenStreetMap (Overpass)</option>
                <option value="google_places">
                  Google Places {providers.find(p => p.provider_id === 'google_places')?.is_configured ? '(Configured)' : '(Not configured)'}
                </option>
              </select>
            </div>

            {/* Business Category */}
            <div>
              <label className="block text-[11px] font-medium text-[#A0A5AD] mb-1">Category</label>
              <input
                type="text"
                list="supported-categories-list"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                placeholder="restaurant, cafe..."
                className="w-full bg-[#111214] border border-[#30343A] rounded px-2.5 py-1.5 text-[12px] text-[#F3F4F6] placeholder-[#575C66] focus:border-[#4B5361] outline-none"
              />
              <datalist id="supported-categories-list">
                {supportedCategories.map((c) => (
                  <option key={c.category} value={c.category}>{c.label}</option>
                ))}
              </datalist>
            </div>

            {/* Country */}
            <div>
              <label className="block text-[11px] font-medium text-[#A0A5AD] mb-1">Country</label>
              <select
                value={country}
                onChange={(e) => setCountry(e.target.value)}
                className="w-full bg-[#111214] border border-[#30343A] rounded px-2.5 py-1.5 text-[12px] text-[#F3F4F6] focus:border-[#4B5361] outline-none"
              >
                <option value="India">India</option>
                <option value="United States">United States</option>
                <option value="United Kingdom">United Kingdom</option>
                <option value="Germany">Germany</option>
                <option value="France">France</option>
              </select>
            </div>

            {/* Region / State */}
            <div>
              <label className="block text-[11px] font-medium text-[#A0A5AD] mb-1">Region / State</label>
              <input
                type="text"
                value={region}
                onChange={(e) => setRegion(e.target.value)}
                placeholder="Maharashtra"
                className="w-full bg-[#111214] border border-[#30343A] rounded px-2.5 py-1.5 text-[12px] text-[#F3F4F6] placeholder-[#575C66] focus:border-[#4B5361] outline-none"
              />
            </div>

            {/* City */}
            <div>
              <label className="block text-[11px] font-medium text-[#A0A5AD] mb-1">City / Locality</label>
              <input
                type="text"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                placeholder="Navi Mumbai"
                className="w-full bg-[#111214] border border-[#30343A] rounded px-2.5 py-1.5 text-[12px] text-[#F3F4F6] placeholder-[#575C66] focus:border-[#4B5361] outline-none"
              />
            </div>

            {/* Website Filter */}
            <div>
              <label className="block text-[11px] font-medium text-[#A0A5AD] mb-1">Website Presence</label>
              <select
                value={conditionFilter}
                onChange={(e) => setConditionFilter(e.target.value)}
                className="w-full bg-[#111214] border border-[#30343A] rounded px-2.5 py-1.5 text-[12px] text-[#F3F4F6] focus:border-[#4B5361] outline-none"
              >
                <option value="all">All listings</option>
                <option value="with_website">With website listed</option>
                <option value="without_website">Website not listed</option>
              </select>
            </div>

            {/* Max Results */}
            <div>
              <label className="block text-[11px] font-medium text-[#A0A5AD] mb-1">Limit</label>
              <select
                value={maxResults}
                onChange={(e) => setMaxResults(e.target.value)}
                className="w-full bg-[#111214] border border-[#30343A] rounded px-2.5 py-1.5 text-[12px] text-[#F3F4F6] focus:border-[#4B5361] outline-none"
              >
                <option value="10">10 results</option>
                <option value="25">25 results</option>
                <option value="50">50 results</option>
                <option value="100">100 results</option>
              </select>
            </div>

            {/* Search Submit Button */}
            <div className="flex flex-col justify-end">
              <Button
                variant="primary"
                size="md"
                onClick={handleSearch}
                isLoading={isSearching}
                leftIcon={<Search className="w-3.5 h-3.5" />}
                className="w-full"
              >
                Find businesses
              </Button>
            </div>
          </div>

          {/* Provider not configured alert */}
          {currentProvider && !currentProvider.is_configured && (
            <div className="flex items-center gap-2 p-2.5 rounded bg-[#2A1818] border border-[#4A2626] text-[12px] text-[#D78383]">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{currentProvider.status_message}</span>
            </div>
          )}

          {/* Unmapped category or approximate mapping warning */}
          {searchWarnings.length > 0 && (
            <div className="flex items-start gap-2 p-2.5 rounded bg-[#2A2417] border border-[#4A3D22] text-[11px] text-[#D8B16C]">
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
              <div className="flex flex-col gap-0.5">
                {searchWarnings.map((w, idx) => (
                  <span key={idx}>{w}</span>
                ))}
              </div>
            </div>
          )}

          {category && !supportedCategories.some(c => c.category.toLowerCase() === category.toLowerCase().trim()) && unmappedGuidance && (
            <div className="flex items-start gap-2 p-2.5 rounded bg-[#1A1C20] border border-[#2B2F36] text-[11px] text-[#A0A5AD]">
              <Info className="w-3.5 h-3.5 text-[#91B7D8] shrink-0 mt-0.5" />
              <span>{unmappedGuidance}</span>
            </div>
          )}
        </div>

        {/* Search Error State */}
        {searchError && (
          <div className="p-4 rounded border border-[#4A2626] bg-[#221515] flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-[#D78383] shrink-0 mt-0.5" />
            <div className="flex flex-col gap-1">
              <div className="text-[13px] font-medium text-[#F3F4F6]">
                Discovery Request Failed
              </div>
              <p className="text-[12px] text-[#D78383] leading-relaxed">
                {searchError}
              </p>
              <div className="text-[11px] text-[#727780] mt-1">
                Results are not fabricated when a real provider request fails. Please check your network connection, refine parameters, or inspect the provider status.
              </div>
            </div>
          </div>
        )}

        {/* Results Card */}
        <div className="flex-1 flex flex-col rounded border border-[#282B31] bg-[#17191C] overflow-hidden">
          {/* Subheader Filter Tabs */}
          <div className="px-4 py-2.5 border-b border-[#24272D] flex flex-wrap items-center justify-between gap-2 bg-[#1D2024]/50">
            <div className="flex items-center gap-1.5 flex-wrap">
              <button
                onClick={() => setActiveTab('all')}
                className={`px-2.5 py-1 rounded text-[12px] font-medium transition-colors ${
                  activeTab === 'all'
                    ? 'bg-[#2B2F36] text-[#F3F4F6]'
                    : 'text-[#A0A5AD] hover:text-[#F3F4F6]'
                }`}
              >
                All Results ({results.length})
              </button>
              <button
                onClick={() => setActiveTab('with_website')}
                className={`px-2.5 py-1 rounded text-[12px] font-medium transition-colors ${
                  activeTab === 'with_website'
                    ? 'bg-[#2B2F36] text-[#F3F4F6]'
                    : 'text-[#A0A5AD] hover:text-[#F3F4F6]'
                }`}
              >
                Website Listed ({results.filter((r) => !!r.website_url).length})
              </button>
              <button
                onClick={() => setActiveTab('not_listed')}
                className={`px-2.5 py-1 rounded text-[12px] font-medium transition-colors ${
                  activeTab === 'not_listed'
                    ? 'bg-[#2B2F36] text-[#F3F4F6]'
                    : 'text-[#A0A5AD] hover:text-[#F3F4F6]'
                }`}
              >
                Website Not Listed ({results.filter((r) => !r.website_url).length})
              </button>
              <button
                onClick={() => setActiveTab('saved')}
                className={`px-2.5 py-1 rounded text-[12px] font-medium transition-colors ${
                  activeTab === 'saved'
                    ? 'bg-[#2B2F36] text-[#F3F4F6]'
                    : 'text-[#A0A5AD] hover:text-[#F3F4F6]'
                }`}
              >
                Saved Prospects ({results.filter((r) => r.is_saved).length})
              </button>
              <button
                onClick={() => setActiveTab('not_saved')}
                className={`px-2.5 py-1 rounded text-[12px] font-medium transition-colors ${
                  activeTab === 'not_saved'
                    ? 'bg-[#2B2F36] text-[#F3F4F6]'
                    : 'text-[#A0A5AD] hover:text-[#F3F4F6]'
                }`}
              >
                Unsaved ({results.filter((r) => !r.is_saved).length})
              </button>
            </div>

            <div className="flex items-center gap-3 text-[12px] text-[#727780]">
              {searchDurationMs !== null && (
                <div>
                  Duration: <strong className="font-mono text-[#A0A5AD]">{searchDurationMs}ms</strong>
                </div>
              )}
            </div>
          </div>

          {/* Results Table */}
          <div className="flex-1 overflow-y-auto">
            <table className="w-full text-left border-collapse text-[12px]">
              <thead className="bg-[#1A1C20] text-[#727780] font-medium border-b border-[#24272D] sticky top-0">
                <tr>
                  <th className="py-2.5 px-4 font-medium">Business</th>
                  <th className="py-2.5 px-3 font-medium">Category</th>
                  <th className="py-2.5 px-3 font-medium">Location</th>
                  <th className="py-2.5 px-3 font-medium">Website</th>
                  <th className="py-2.5 px-3 font-medium">Website Classification</th>
                  <th className="py-2.5 px-3 font-medium">Source</th>
                  <th className="py-2.5 px-4 text-right font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#202328] bg-[#17191C]">
                {visibleResults.map((item) => (
                  <tr key={item.id} className="hover:bg-[#1C1F24] transition-colors">
                    <td className="py-2.5 px-4 font-medium text-[#F3F4F6]">
                      <div className="flex items-center gap-2">
                        <Building2 className="w-3.5 h-3.5 text-[#727780] shrink-0" />
                        <span className="truncate max-w-[180px]">{item.name}</span>
                        {item.raw_metadata?.rating && (
                          <span className="text-[10px] font-mono text-[#D8B16C] bg-[#272318] px-1 py-0.2 rounded border border-[#3E341E]">
                            ★ {item.raw_metadata.rating}
                          </span>
                        )}
                      </div>
                    </td>

                    <td className="py-2.5 px-3 text-[#A0A5AD]">{item.category}</td>

                    <td className="py-2.5 px-3 text-[#A0A5AD]">
                      {item.location.city ? `${item.location.city}, ${item.location.state}` : item.location.country}
                    </td>

                    <td className="py-2.5 px-3">
                      {item.website_url ? (
                        <a
                          href={item.website_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-mono text-[11px] text-[#91B7D8] hover:underline flex items-center gap-1"
                        >
                          {item.website_url.replace(/https?:\/\//, '').replace(/\/$/, '')}
                          <ExternalLink className="w-3 h-3 shrink-0" />
                        </a>
                      ) : (
                        <span className="text-[11px] text-[#727780] italic">
                          Website not listed — verification required
                        </span>
                      )}
                    </td>

                    <td className="py-2.5 px-3">
                      <Badge variant="website" websiteStatus={item.website_status} size="sm" />
                    </td>

                    <td className="py-2.5 px-3">
                      <span className="text-[11px] font-mono text-[#727780] bg-[#1E2024] px-1.5 py-0.5 rounded border border-[#2B2F36]">
                        {item.source_provider.toUpperCase()}
                      </span>
                    </td>

                    <td className="py-2.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setInspectItem(item)}
                          title="Inspect full provider metadata"
                        >
                          <Eye className="w-3 h-3" />
                        </Button>

                        {/* Audit action - Only available if valid website exists */}
                        {item.website_url ? (
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => handleRunAuditForDiscovered(item)}
                            leftIcon={<Play className="w-3 h-3 text-[#D8E7A2]" />}
                            title="Execute live website audit crawl"
                          >
                            Audit
                          </Button>
                        ) : null}

                        {/* Save or Open */}
                        {item.is_saved ? (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => item.matched_existing_id && handleOpenProspect(item.matched_existing_id)}
                            leftIcon={<Check className="w-3 h-3 text-[#80B89A]" />}
                            className="text-[#80B89A] border border-[#253D30]"
                          >
                            Saved
                          </Button>
                        ) : (
                          <Button
                            variant="primary"
                            size="sm"
                            isLoading={isSavingId === item.id}
                            onClick={() => handleSaveProspect(item)}
                            leftIcon={<Plus className="w-3 h-3" />}
                          >
                            Save
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}

                {visibleResults.length === 0 && (
                  <tr>
                    <td colSpan={7} className="py-12 text-center text-[#727780]">
                      <div className="flex flex-col items-center gap-2 max-w-md mx-auto">
                        <Compass className="w-8 h-8 text-[#30343A]" />
                        <div className="text-[13px] text-[#F3F4F6] font-medium">
                          {hasSearched ? 'No matching businesses returned by provider' : 'Run a query to discover real businesses'}
                        </div>
                        <p className="text-[11px] text-[#727780] leading-relaxed">
                          {hasSearched
                            ? `The provider returned 0 records for "${category}" in "${city}". Try a broader category such as "office", "shop", or "restaurant", or check your geographic locality.`
                            : 'Select a category, location, and provider above, then click "Find businesses" to query live records.'}
                        </p>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Provider Legal Attribution Footer */}
          <div className="px-4 py-2 border-t border-[#24272D] bg-[#141618] flex items-center justify-between text-[11px] text-[#727780]">
            <div className="flex items-center gap-1.5">
              <span>Attribution:</span>
              <span className="text-[#A0A5AD]">
                {currentProvider?.attribution || 'Data © OpenStreetMap contributors, ODbL 1.0'}
              </span>
            </div>
            <a
              href="https://www.openstreetmap.org/copyright"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#91B7D8] hover:underline flex items-center gap-1"
            >
              OSM License Information <ExternalLink className="w-2.5 h-2.5" />
            </a>
          </div>
        </div>
      </div>

      {/* Inspect Item Detail Modal */}
      {inspectItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4">
          <div 
            className="w-full max-w-2xl rounded-lg border border-[#30343A] bg-[#17191C] shadow-2xl overflow-hidden flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between px-5 py-3.5 border-b border-[#24272D] bg-[#141619]">
              <div className="flex items-center gap-2">
                <Building2 className="w-4 h-4 text-[#D8E7A2]" />
                <h3 className="text-[14px] font-semibold text-[#F3F4F6]">
                  {inspectItem.name}
                </h3>
              </div>
              <button
                onClick={() => setInspectItem(null)}
                className="p-1 rounded text-[#727780] hover:text-[#F3F4F6] hover:bg-[#202328]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-5 flex flex-col gap-4 max-h-[70vh] overflow-y-auto text-[12px]">
              <div className="grid grid-cols-2 gap-3 p-3 rounded bg-[#141618] border border-[#262A30]">
                <div>
                  <span className="text-[11px] text-[#727780]">Category:</span>
                  <div className="text-[#F3F4F6] font-medium mt-0.5">{inspectItem.category}</div>
                </div>
                <div>
                  <span className="text-[11px] text-[#727780]">Website Status:</span>
                  <div className="mt-0.5">
                    <Badge variant="website" websiteStatus={inspectItem.website_status} size="sm" />
                  </div>
                </div>
                <div>
                  <span className="text-[11px] text-[#727780]">Location:</span>
                  <div className="text-[#A0A5AD] mt-0.5 flex items-center gap-1">
                    <MapPin className="w-3 h-3 text-[#727780]" />
                    {inspectItem.location.address || `${inspectItem.location.city}, ${inspectItem.location.state}`}
                  </div>
                </div>
                <div>
                  <span className="text-[11px] text-[#727780]">Coordinates:</span>
                  <div className="font-mono text-[#727780] text-[11px] mt-0.5">
                    {inspectItem.location.latitude && inspectItem.location.longitude 
                      ? `${inspectItem.location.latitude.toFixed(4)}, ${inspectItem.location.longitude.toFixed(4)}`
                      : 'Not provided'}
                  </div>
                </div>
              </div>

              {/* Website & Contacts */}
              <div className="flex flex-col gap-1.5 p-3 rounded bg-[#141618] border border-[#262A30]">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-[#727780]">Registered Website:</span>
                  {inspectItem.website_url ? (
                    <a
                      href={inspectItem.website_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-mono text-[11px] text-[#91B7D8] hover:underline flex items-center gap-1"
                    >
                      {inspectItem.website_url}
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  ) : (
                    <span className="text-[#727780] italic">Website not listed — verification required</span>
                  )}
                </div>

                {inspectItem.phone && (
                  <div className="flex items-center justify-between text-[#A0A5AD]">
                    <span className="text-[11px] text-[#727780] flex items-center gap-1">
                      <Phone className="w-3 h-3" /> Telephone:
                    </span>
                    <span className="font-mono">{inspectItem.phone}</span>
                  </div>
                )}

                {inspectItem.email && (
                  <div className="flex items-center justify-between text-[#A0A5AD]">
                    <span className="text-[11px] text-[#727780] flex items-center gap-1">
                      <Mail className="w-3 h-3" /> Email:
                    </span>
                    <span className="font-mono">{inspectItem.email}</span>
                  </div>
                )}
              </div>

              {/* Provider Metadata */}
              <div className="p-3 rounded bg-[#141618] border border-[#262A30] flex flex-col gap-2">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-[#727780]">Source Provider:</span>
                  <span className="font-mono text-[#D8E7A2]">{inspectItem.source_provider}</span>
                </div>
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-[#727780]">Record Identifier:</span>
                  <span className="font-mono text-[#A0A5AD]">{inspectItem.source_record_id || 'N/A'}</span>
                </div>
                {inspectItem.source_url && (
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-[#727780]">Source Web Entity:</span>
                    <a
                      href={inspectItem.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[#91B7D8] hover:underline flex items-center gap-1"
                    >
                      Open in {inspectItem.source_provider.toUpperCase()} <ExternalLink className="w-2.5 h-2.5" />
                    </a>
                  </div>
                )}
                <div className="text-[10px] text-[#727780] mt-1 pt-1 border-t border-[#262A30]">
                  {inspectItem.attribution}
                </div>
              </div>

              {/* Duplicate Information */}
              {inspectItem.is_saved && (
                <div className="p-2.5 rounded bg-[#18261F] border border-[#253E31] text-[11px] text-[#80B89A] flex items-center justify-between">
                  <span>Already saved in pipeline (ID: {inspectItem.matched_existing_id})</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      if (inspectItem.matched_existing_id) {
                        handleOpenProspect(inspectItem.matched_existing_id);
                        setInspectItem(null);
                      }
                    }}
                  >
                    View in Prospects
                  </Button>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-end gap-2 px-5 py-3 border-t border-[#24272D] bg-[#141619]">
              <Button variant="ghost" size="md" onClick={() => setInspectItem(null)}>
                Close
              </Button>
              {inspectItem.website_url && (
                <Button
                  variant="secondary"
                  size="md"
                  onClick={() => {
                    handleRunAuditForDiscovered(inspectItem);
                    setInspectItem(null);
                  }}
                  leftIcon={<Play className="w-3.5 h-3.5 text-[#D8E7A2]" />}
                >
                  Run Website Audit
                </Button>
              )}
              {!inspectItem.is_saved && (
                <Button
                  variant="primary"
                  size="md"
                  onClick={() => handleSaveProspect(inspectItem)}
                  leftIcon={<Plus className="w-3.5 h-3.5" />}
                >
                  Save as Prospect
                </Button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

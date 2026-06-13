// frontend/src/App.tsx
import { useState, useEffect } from 'react';
import { 
  BarChart3, 
  Users, 
  ShieldAlert, 
  Gem, 
  Scale, 
  Search, 
  ChevronLeft, 
  ChevronRight, 
  Sliders, 
  X, 
  ArrowRightLeft, 
  CheckCircle2, 
  AlertTriangle
} from 'lucide-react';
import { Radar, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement
} from 'chart.js';

// Register Chart.js modules
ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement
);

const API_BASE = 'http://127.0.0.1:8000';

function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'rankings' | 'gems' | 'honeypots' | 'compare'>('dashboard');
  
  // Dashboard Stats
  const [stats, setStats] = useState<any>(null);
  
  // Rankings State
  const [rankings, setRankings] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  
  // Weight Sliders
  const [weights, setWeights] = useState({
    semantic: 35,
    behavior: 20,
    growth: 15,
    leadership: 10,
    startup: 10,
    hidden_gem: 5,
    honeypot_penalty: 5
  });

  // Selected candidate for Side Drawer
  const [selectedCandidate, setSelectedCandidate] = useState<any>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  
  // Comparison State
  const [compareAId, setCompareAId] = useState('');
  const [compareBId, setCompareBId] = useState('');
  const [comparisonResult, setComparisonResult] = useState<any>(null);
  const [compareError, setCompareError] = useState<string | null>(null);

  // Hidden Gems & Honeypots
  const [gemsList, setGemsList] = useState<any[]>([]);
  const [honeypotsList, setHoneypotsList] = useState<any[]>([]);

  // Fetch Dashboard Stats
  useEffect(() => {
    fetch(`${API_BASE}/api/dashboard`)
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(err => console.error(err));
  }, []);

  // Fetch Rankings
  useEffect(() => {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: '10',
      semantic_w: (weights.semantic / 100).toString(),
      behavior_w: (weights.behavior / 100).toString(),
      growth_w: (weights.growth / 100).toString(),
      leadership_w: (weights.leadership / 100).toString(),
      startup_w: (weights.startup / 100).toString(),
      hidden_gem_w: (weights.hidden_gem / 100).toString(),
      honeypot_w: (weights.honeypot_penalty / 100).toString()
    });
    if (searchQuery) params.append('search', searchQuery);

    fetch(`${API_BASE}/api/rank?${params.toString()}`)
      .then(res => res.json())
      .then(data => {
        setRankings(data.candidates);
        setTotalPages(Math.ceil(data.total / data.limit));
      })
      .catch(err => console.error(err));
  }, [page, weights, searchQuery]);

  // Fetch Hidden Gems and Honeypots
  useEffect(() => {
    if (activeTab === 'gems') {
      fetch(`${API_BASE}/api/hidden-gems`)
        .then(res => res.json())
        .then(data => setGemsList(data))
        .catch(err => console.error(err));
    } else if (activeTab === 'honeypots') {
      fetch(`${API_BASE}/api/honeypot`)
        .then(res => res.json())
        .then(data => setHoneypotsList(data))
        .catch(err => console.error(err));
    }
  }, [activeTab]);

  // Handle Candidate Detail Drawer View
  const handleViewCandidate = (id: string) => {
    fetch(`${API_BASE}/api/candidate/${id}`)
      .then(res => res.json())
      .then(data => {
        setSelectedCandidate(data);
        setDrawerOpen(true);
      })
      .catch(err => console.error(err));
  };

  // Handle Comparison Fetch
  const handleCompare = () => {
    if (!compareAId || !compareBId) return;
    setCompareError(null);
    setComparisonResult(null);
    fetch(`${API_BASE}/api/compare?id_a=${compareAId}&id_b=${compareBId}`)
      .then(async res => {
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || 'Failed to fetch comparison details.');
        }
        return data;
      })
      .then(data => setComparisonResult(data))
      .catch(err => {
        console.error(err);
        setCompareError(err.message || 'An unexpected error occurred.');
      });
  };

  const handleWeightChange = (key: keyof typeof weights, value: number) => {
    setWeights(prev => ({
      ...prev,
      [key]: value
    }));
    setPage(1);
  };

  // Chart Data Configurations
  const expChartData = stats ? {
    labels: Object.keys(stats.experience_distribution),
    datasets: [{
      label: 'Candidates Count',
      data: Object.values(stats.experience_distribution),
      backgroundColor: 'rgba(0, 242, 254, 0.4)',
      borderColor: '#00f2fe',
      borderWidth: 1.5,
      borderRadius: 6,
    }]
  } : null;

  const radarChartData = selectedCandidate ? {
    labels: ['Technical', 'Leadership', 'Innovation', 'Communication', 'Learning', 'Startup', 'Domain'],
    datasets: [
      {
        label: selectedCandidate.anonymized_name,
        data: [
          selectedCandidate.dna.technical_dna,
          selectedCandidate.dna.leadership_dna,
          selectedCandidate.dna.innovation_dna,
          selectedCandidate.dna.communication_dna,
          selectedCandidate.dna.learning_dna,
          selectedCandidate.dna.startup_dna,
          selectedCandidate.dna.domain_dna
        ],
        backgroundColor: 'rgba(0, 242, 254, 0.2)',
        borderColor: '#00f2fe',
        pointBackgroundColor: '#00f2fe',
        borderWidth: 2,
      }
    ]
  } : null;

  const compareRadarData = comparisonResult ? {
    labels: ['Technical', 'Leadership', 'Innovation', 'Communication', 'Learning', 'Startup', 'Domain'],
    datasets: [
      {
        label: comparisonResult.candidate_a.anonymized_name,
        data: [
          comparisonResult.candidate_a.dna.technical_dna,
          comparisonResult.candidate_a.dna.leadership_dna,
          comparisonResult.candidate_a.dna.innovation_dna,
          comparisonResult.candidate_a.dna.communication_dna,
          comparisonResult.candidate_a.dna.learning_dna,
          comparisonResult.candidate_a.dna.startup_dna,
          comparisonResult.candidate_a.dna.domain_dna
        ],
        backgroundColor: 'rgba(79, 172, 254, 0.2)',
        borderColor: '#4facfe',
        pointBackgroundColor: '#4facfe',
        borderWidth: 2,
      },
      {
        label: comparisonResult.candidate_b.anonymized_name,
        data: [
          comparisonResult.candidate_b.dna.technical_dna,
          comparisonResult.candidate_b.dna.leadership_dna,
          comparisonResult.candidate_b.dna.innovation_dna,
          comparisonResult.candidate_b.dna.communication_dna,
          comparisonResult.candidate_b.dna.learning_dna,
          comparisonResult.candidate_b.dna.startup_dna,
          comparisonResult.candidate_b.dna.domain_dna
        ],
        backgroundColor: 'rgba(161, 140, 209, 0.2)',
        borderColor: '#a18cd1',
        pointBackgroundColor: '#a18cd1',
        borderWidth: 2,
      }
    ]
  } : null;

  return (
    <div className="app-container">
      {/* Sidebar navigation */}
      <div className="sidebar">
        <div className="logo-section">
          <div className="logo-icon">S</div>
          <div>
            <div className="logo-text">SYNAPTIQ</div>
            <div className="logo-subtext">Hiring Engine</div>
          </div>
        </div>

        <div className="nav-links">
          <div 
            className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <BarChart3 size={18} />
            <span>Overview</span>
          </div>
          <div 
            className={`nav-item ${activeTab === 'rankings' ? 'active' : ''}`}
            onClick={() => setActiveTab('rankings')}
          >
            <Users size={18} />
            <span>Talent Rankings</span>
          </div>
          <div 
            className={`nav-item ${activeTab === 'gems' ? 'active' : ''}`}
            onClick={() => setActiveTab('gems')}
          >
            <Gem size={18} />
            <span>Hidden Gems</span>
          </div>
          <div 
            className={`nav-item ${activeTab === 'honeypots' ? 'active' : ''}`}
            onClick={() => setActiveTab('honeypots')}
          >
            <ShieldAlert size={18} />
            <span>Honeypots</span>
          </div>
          <div 
            className={`nav-item ${activeTab === 'compare' ? 'active' : ''}`}
            onClick={() => setActiveTab('compare')}
          >
            <Scale size={18} />
            <span>Candidate Compare</span>
          </div>
        </div>
      </div>

      {/* Main content window */}
      <div className="main-content">
        
        {/* TAB 1: OVERVIEW DASHBOARD */}
        {activeTab === 'dashboard' && (
          <div>
            <div className="page-header">
              <div className="page-title">
                <h1>Predicting Human Potential</h1>
                <p>Neural Talent & Behavioral Intelligence Dashboard</p>
              </div>
            </div>

            {/* KPI metrics row */}
            {stats && (
              <div className="kpi-grid">
                <div className="glass-card kpi-card">
                  <div>
                    <div className="kpi-label">Candidates Scanned</div>
                    <div className="kpi-value">{stats.total_candidates_scanned.toLocaleString()}</div>
                  </div>
                  <div className="kpi-icon blue"><Users size={24} /></div>
                </div>
                <div className="glass-card kpi-card">
                  <div>
                    <div className="kpi-label">Honeypots Blocked</div>
                    <div className="kpi-value">{stats.honeypots_blocked}</div>
                  </div>
                  <div className="kpi-icon danger"><ShieldAlert size={24} /></div>
                </div>
                <div className="glass-card kpi-card">
                  <div>
                    <div className="kpi-label">Hidden Gems Found</div>
                    <div className="kpi-value">{stats.hidden_gems_discovered}</div>
                  </div>
                  <div className="kpi-icon violet"><Gem size={24} /></div>
                </div>
                <div className="glass-card kpi-card">
                  <div>
                    <div className="kpi-label">Talent Index Average</div>
                    <div className="kpi-value">{stats.avg_talent_index}%</div>
                  </div>
                  <div className="kpi-icon success"><CheckCircle2 size={24} /></div>
                </div>
              </div>
            )}

            {/* Charts section */}
            <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '32px', marginTop: '32px' }}>
              <div className="glass-card">
                <h3 style={{ marginBottom: '20px' }}>Workforce Experience Distribution</h3>
                {expChartData && (
                  <div style={{ height: '300px' }}>
                    <Bar 
                      data={expChartData} 
                      options={{ 
                        responsive: true, 
                        maintainAspectRatio: false,
                        scales: {
                          y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#94a3b8' } },
                          x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
                        },
                        plugins: { legend: { display: false } }
                      }} 
                    />
                  </div>
                )}
              </div>

              <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <h3 style={{ marginBottom: '16px' }}>Hiring Blueprint Settings</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '20px' }}>
                  The AI engine screens candidate profiles against the parsed job blueprint for the **Senior AI Engineer - Founding Team** role.
                </p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px', borderBottom: '1px solid var(--border-color)' }}>
                    <span>Target Experience:</span>
                    <span style={{ color: 'var(--neon-cyan)', fontWeight: 600 }}>5 - 9 Years</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px', borderBottom: '1px solid var(--border-color)' }}>
                    <span>Required Tech Stack:</span>
                    <span style={{ color: 'var(--text-secondary)', fontSize: '12px', textAlign: 'right' }}>Embeddings, Vector DBs, Python, NDCG</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px', borderBottom: '1px solid var(--border-color)' }}>
                    <span>Blocked Traps:</span>
                    <span style={{ color: 'var(--color-danger)', fontWeight: 600 }}>Keyword Stuffers, Chrono Inconsistencies</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: CANDIDATE RANKINGS */}
        {activeTab === 'rankings' && (
          <div>
            <div className="page-header">
              <div className="page-title">
                <h1>Explainable Talent Rankings</h1>
                <p>Dynamically score and rank candidate pool based on custom weights</p>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: '32px' }}>
              
              {/* Sliders sidebar control */}
              <div className="glass-card" style={{ height: 'fit-content' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '24px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
                  <Sliders size={18} style={{ color: 'var(--neon-cyan)' }} />
                  <h3 style={{ fontSize: '16px' }}>Recruiter Controls</h3>
                </div>

                <div className="slider-container">
                  <div className="slider-header">
                    <span>Semantic Match</span>
                    <span>{weights.semantic}%</span>
                  </div>
                  <input 
                    type="range" min="0" max="100" className="slider-input" 
                    value={weights.semantic} 
                    onChange={(e) => handleWeightChange('semantic', parseInt(e.target.value))}
                  />
                </div>

                <div className="slider-container">
                  <div className="slider-header">
                    <span>Behavioral Signals</span>
                    <span>{weights.behavior}%</span>
                  </div>
                  <input 
                    type="range" min="0" max="100" className="slider-input" 
                    value={weights.behavior} 
                    onChange={(e) => handleWeightChange('behavior', parseInt(e.target.value))}
                  />
                </div>

                <div className="slider-container">
                  <div className="slider-header">
                    <span>Career Growth</span>
                    <span>{weights.growth}%</span>
                  </div>
                  <input 
                    type="range" min="0" max="100" className="slider-input" 
                    value={weights.growth} 
                    onChange={(e) => handleWeightChange('growth', parseInt(e.target.value))}
                  />
                </div>

                <div className="slider-container">
                  <div className="slider-header">
                    <span>Leadership Potential</span>
                    <span>{weights.leadership}%</span>
                  </div>
                  <input 
                    type="range" min="0" max="100" className="slider-input" 
                    value={weights.leadership} 
                    onChange={(e) => handleWeightChange('leadership', parseInt(e.target.value))}
                  />
                </div>

                <div className="slider-container">
                  <div className="slider-header">
                    <span>Startup Readiness</span>
                    <span>{weights.startup}%</span>
                  </div>
                  <input 
                    type="range" min="0" max="100" className="slider-input" 
                    value={weights.startup} 
                    onChange={(e) => handleWeightChange('startup', parseInt(e.target.value))}
                  />
                </div>
              </div>

              {/* Table results list */}
              <div className="glass-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: '16px', marginBottom: '24px' }}>
                  <div style={{ display: 'flex', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '8px 12px', background: 'rgba(0,0,0,0.2)', width: '320px', alignItems: 'center', gap: '8px' }}>
                    <Search size={16} style={{ color: 'var(--text-muted)' }} />
                    <input 
                      type="text" placeholder="Search name or title..." 
                      style={{ background: 'none', border: 'none', color: '#fff', outline: 'none', fontSize: '13px', width: '100%' }}
                      value={searchQuery}
                      onChange={(e) => { setSearchQuery(e.target.value); setPage(1); }}
                    />
                  </div>
                </div>

                <div className="table-container">
                  <table className="custom-table">
                    <thead>
                      <tr>
                        <th>Rank</th>
                        <th>Candidate</th>
                        <th>Title</th>
                        <th>Experience</th>
                        <th>Match Score</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rankings.map((c) => (
                        <tr key={c.candidate_id}>
                          <td>
                            <span style={{ 
                              fontWeight: 700, 
                              color: c.rank <= 3 ? 'var(--neon-cyan)' : 'var(--text-secondary)' 
                            }}>
                              #{c.rank}
                            </span>
                          </td>
                          <td>
                            <div style={{ fontWeight: 600 }}>{c.anonymized_name}</div>
                            <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{c.candidate_id}</div>
                          </td>
                          <td>{c.current_title}</td>
                          <td>{c.years_of_experience} Yrs</td>
                          <td>
                            <span style={{ fontWeight: 600, color: 'var(--color-success)' }}>
                              {(c.score * 100).toFixed(1)}%
                            </span>
                          </td>
                          <td>
                            <button className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '12px' }} onClick={() => handleViewCandidate(c.candidate_id)}>
                              Explain
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Pagination footer */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '24px', borderTop: '1px solid var(--border-color)', paddingTop: '16px' }}>
                  <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                    Page {page} of {totalPages}
                  </span>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button 
                      className="btn btn-secondary" style={{ padding: '6px 12px' }}
                      disabled={page === 1}
                      onClick={() => setPage(prev => Math.max(1, prev - 1))}
                    >
                      <ChevronLeft size={16} />
                    </button>
                    <button 
                      className="btn btn-secondary" style={{ padding: '6px 12px' }}
                      disabled={page === totalPages}
                      onClick={() => setPage(prev => Math.min(totalPages, prev + 1))}
                    >
                      <ChevronRight size={16} />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: HIDDEN GEMS */}
        {activeTab === 'gems' && (
          <div>
            <div className="page-header">
              <div className="page-title">
                <h1>Hidden Talent Discovery <span style={{ fontSize: '14px', color: 'var(--text-secondary)', fontWeight: 'normal' }}>(Top 250 Displayed)</span></h1>
                <p>Identified high-potential candidates that typical ATS keyword matchers bypass</p>
              </div>
            </div>

            <div className="glass-card">
              <div className="table-container">
                <table className="custom-table">
                  <thead>
                    <tr>
                      <th>Candidate ID</th>
                      <th>Anonymized Name</th>
                      <th>Generic Title</th>
                      <th>Experience</th>
                      <th>Talent Index</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {gemsList.map((c) => (
                      <tr key={c.candidate_id}>
                        <td><span style={{ fontWeight: 600 }}>{c.candidate_id}</span></td>
                        <td><div style={{ fontWeight: 600 }}>{c.anonymized_name}</div></td>
                        <td><span className="badge info">{c.current_title}</span></td>
                        <td>{c.years_of_experience} Yrs</td>
                        <td><span style={{ color: 'var(--color-success)', fontWeight: 600 }}>{(c.score * 100).toFixed(1)}%</span></td>
                        <td>
                          <button className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '12px' }} onClick={() => handleViewCandidate(c.candidate_id)}>
                            Explain
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: HONEYPOTS BLOCKED */}
        {activeTab === 'honeypots' && (
          <div>
            <div className="page-header">
              <div className="page-title">
                <h1>Fraud & Honeypots <span style={{ fontSize: '14px', color: 'var(--text-secondary)', fontWeight: 'normal' }}>(Top 250 Displayed)</span></h1>
                <p>Candidates blocked due to skill inflation, suspicious timelines, or generative AI abuse</p>
              </div>
            </div>

            <div className="glass-card">
              <div className="table-container">
                <table className="custom-table">
                  <thead>
                    <tr>
                      <th>Candidate ID</th>
                      <th>Name</th>
                      <th>Conflict Details</th>
                      <th>Risk Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {honeypotsList.map((c) => (
                      <tr key={c.candidate_id}>
                        <td style={{ verticalAlign: 'top' }}><span style={{ fontWeight: 600 }}>{c.candidate_id}</span></td>
                        <td style={{ verticalAlign: 'top' }}><div style={{ fontWeight: 600 }}>{c.anonymized_name}</div></td>
                        <td>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                            {c.honeypot_reasons.map((r: string, idx: number) => (
                              <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-danger)', fontSize: '13px' }}>
                                <AlertTriangle size={14} />
                                <span>{r}</span>
                              </div>
                            ))}
                          </div>
                        </td>
                        <td style={{ verticalAlign: 'top' }}><span className="badge danger">Extreme (100%)</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB 5: CANDIDATE COMPARISON */}
        {activeTab === 'compare' && (
          <div>
            <div className="page-header">
              <div className="page-title">
                <h1>Side-by-Side Candidate Comparison</h1>
                <p>Direct comparison of qualifications, talent genomes, and behavioral stats</p>
              </div>
            </div>

            <div className="glass-card" style={{ marginBottom: '32px' }}>
              <div style={{ display: 'flex', gap: '24px', alignItems: 'flex-end' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1 }}>
                  <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Candidate ID A:</label>
                  <input 
                    type="text" placeholder="e.g. CAND_0000001" 
                    className="slider-input" style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)', borderRadius: '6px', height: '38px', padding: '0 12px', color: '#fff' }}
                    value={compareAId} onChange={e => setCompareAId(e.target.value)}
                  />
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1 }}>
                  <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Candidate ID B:</label>
                  <input 
                    type="text" placeholder="e.g. CAND_0000002" 
                    className="slider-input" style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)', borderRadius: '6px', height: '38px', padding: '0 12px', color: '#fff' }}
                    value={compareBId} onChange={e => setCompareBId(e.target.value)}
                  />
                </div>
                <button className="btn btn-primary" style={{ height: '38px' }} onClick={handleCompare}>
                  <ArrowRightLeft size={16} />
                  Compare
                </button>
              </div>
            </div>

            {compareError && (
              <div className="glass-card" style={{ borderLeft: '4px solid var(--color-danger)', padding: '16px', marginBottom: '32px', display: 'flex', alignItems: 'center', gap: '12px' }}>
                <AlertTriangle size={20} style={{ color: 'var(--color-danger)' }} />
                <div>
                  <h4 style={{ margin: 0, color: 'var(--color-danger)' }}>Comparison Error</h4>
                  <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: 'var(--text-secondary)' }}>{compareError}</p>
                </div>
              </div>
            )}

            {comparisonResult && (
              <div className="compare-container">
                
                {/* Visual Radar chart comparison */}
                <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                  <h3>Talent Genome Overlap</h3>
                  {compareRadarData && (
                    <div style={{ height: '350px', width: '100%', marginTop: '20px' }}>
                      <Radar 
                        data={compareRadarData} 
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          scales: {
                            r: {
                              grid: { color: 'rgba(255, 255, 255, 0.05)' },
                              angleLines: { color: 'rgba(255, 255, 255, 0.05)' },
                              pointLabels: { color: '#94a3b8', font: { size: 10 } },
                              ticks: { display: false }
                            }
                          },
                          plugins: { legend: { labels: { color: '#f8fafc' } } }
                        }}
                      />
                    </div>
                  )}
                </div>

                {/* Score differences details panel */}
                <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                  <h3>Qualifications Analysis</h3>
                  
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 120px 120px', gap: '16px', borderBottom: '1px solid var(--border-color)', paddingBottom: '10px', fontWeight: 600 }}>
                    <span>Metric</span>
                    <span style={{ color: '#4facfe' }}>{comparisonResult.candidate_a.anonymized_name}</span>
                    <span style={{ color: '#a18cd1' }}>{comparisonResult.candidate_b.anonymized_name}</span>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 120px 120px', gap: '16px', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px' }}>
                    <span>Title</span>
                    <span>{comparisonResult.candidate_a.current_title}</span>
                    <span>{comparisonResult.candidate_b.current_title}</span>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 120px 120px', gap: '16px', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px' }}>
                    <span>Experience</span>
                    <span>{comparisonResult.candidate_a.years_of_experience} Yrs</span>
                    <span>{comparisonResult.candidate_b.years_of_experience} Yrs</span>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 120px 120px', gap: '16px', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px' }}>
                    <span>Technical DNA</span>
                    <span>{comparisonResult.candidate_a.dna.technical_dna}%</span>
                    <span>{comparisonResult.candidate_b.dna.technical_dna}%</span>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 120px 120px', gap: '16px', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px' }}>
                    <span>Startup Readiness</span>
                    <span>{comparisonResult.candidate_a.dna.startup_dna}%</span>
                    <span>{comparisonResult.candidate_b.dna.startup_dna}%</span>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 120px 120px', gap: '16px', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px' }}>
                    <span>Leadership potential</span>
                    <span>{comparisonResult.candidate_a.dna.leadership_dna}%</span>
                    <span>{comparisonResult.candidate_b.dna.leadership_dna}%</span>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 120px 120px', gap: '16px', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px' }}>
                    <span>Talent Index</span>
                    <span style={{ color: 'var(--color-success)', fontWeight: 600 }}>{(comparisonResult.candidate_a.score * 100).toFixed(1)}%</span>
                    <span style={{ color: 'var(--color-success)', fontWeight: 600 }}>{(comparisonResult.candidate_b.score * 100).toFixed(1)}%</span>
                  </div>
                </div>

              </div>
            )}
          </div>
        )}

      </div>

      {/* Side drawer detailed view */}
      {drawerOpen && selectedCandidate && (
        <div className="drawer-backdrop" onClick={() => setDrawerOpen(false)}>
          <div className="drawer" onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
              <h2 style={{ fontSize: '24px' }}>Talent Explainability</h2>
              <X size={20} style={{ cursor: 'pointer', color: 'var(--text-secondary)' }} onClick={() => setDrawerOpen(false)} />
            </div>

            <div style={{ marginBottom: '24px', paddingBottom: '20px', borderBottom: '1px solid var(--border-color)' }}>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--neon-cyan)' }}>{selectedCandidate.anonymized_name}</div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '14px', margin: '4px 0 12px' }}>{selectedCandidate.current_title} | {selectedCandidate.years_of_experience} Years Exp</div>
              <div className="badge success" style={{ padding: '6px 12px', fontSize: '13px' }}>
                Synaptiq Rank Score: {(selectedCandidate.score * 100).toFixed(1)}%
              </div>
            </div>

            {/* Radar chart of genome */}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: '32px' }}>
              <h4 style={{ marginBottom: '16px' }}>Talent Genome</h4>
              {radarChartData && (
                <div style={{ height: '240px', width: '100%' }}>
                  <Radar 
                    data={radarChartData} 
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      scales: {
                        r: {
                          grid: { color: 'rgba(255, 255, 255, 0.05)' },
                          angleLines: { color: 'rgba(255, 255, 255, 0.05)' },
                          pointLabels: { color: '#94a3b8', font: { size: 9 } },
                          ticks: { display: false }
                        }
                      },
                      plugins: { legend: { display: false } }
                    }}
                  />
                </div>
              )}
            </div>

            {/* AI Decision Reasoning details */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div className="glass-card" style={{ borderLeft: '4px solid var(--neon-cyan)', padding: '16px' }}>
                <h4 style={{ marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <CheckCircle2 size={16} style={{ color: 'var(--neon-cyan)' }} />
                  AI Justification Reasoning
                </h4>
                <p style={{ fontSize: '14px', lineHeight: 1.6 }}>{selectedCandidate.reasoning}</p>
              </div>

              <div>
                <h4 style={{ marginBottom: '10px' }}>Career Forecast</h4>
                <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>{selectedCandidate.trajectory.career_forecast}</p>
              </div>

              <div>
                <h4 style={{ marginBottom: '10px' }}>Behavioral Profile</h4>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '13px' }}>
                  <div style={{ background: 'rgba(255,255,255,0.02)', padding: '10px', borderRadius: '6px' }}>
                    <div style={{ color: 'var(--text-secondary)' }}>Notice Period:</div>
                    <div style={{ fontWeight: 600, color: 'var(--neon-cyan)' }}>{selectedCandidate.dna.domain_dna > 50 ? '30 Days' : '60 Days'}</div>
                  </div>
                  <div style={{ background: 'rgba(255,255,255,0.02)', padding: '10px', borderRadius: '6px' }}>
                    <div style={{ color: 'var(--text-secondary)' }}>Relocation Interest:</div>
                    <div style={{ fontWeight: 600 }}>Willing to Relocate</div>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}

export default App;

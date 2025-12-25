import { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import "@/App.css";
import axios from "axios";
import { Phone, Mail, Clock, ChevronUp, ChevronDown, Search, Filter, Plus, PhoneCall, PhoneOff, X, Minus, Maximize2, Calendar } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Shared Dialing Modal Component
const DialingModal = ({ isOpen, lead, callInProgress, onClose, onStartCall, onEndCall }) => {
  if (!isOpen || !lead) return null;

  return createPortal(
    <div className="modal-overlay" onClick={onClose} data-testid="modal-overlay">
      <div className="modal-content dialing-dialog" onClick={(e) => e.stopPropagation()} data-testid="dialing-dialog">
        <div className="modal-header">
          <h2>{callInProgress ? 'Calling...' : 'Dial Number'}</h2>
          <button type="button" className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>
        
        <div className="dialing-content">
          <div className="contact-info">
            <div className="contact-avatar">
              {(lead.lead_name === 'N/A' || !lead.lead_name) ? '?' : lead.lead_name.charAt(0)}
            </div>
            <div className="contact-details">
              <h3>{lead.client_name || lead.lead_name || 'N/A'}</h3>
              <p className="partner">{lead.company_name || lead.partner_name}</p>
            </div>
          </div>
          
          <div className="phone-number" data-testid="dialing-number">
            <Phone size={24} />
            <span>{lead.mobile}</span>
          </div>
          
          {callInProgress && (
            <div className="calling-animation">
              <div className="pulse-ring"></div>
              <div className="pulse-ring delay-1"></div>
              <div className="pulse-ring delay-2"></div>
              <Phone size={40} className="calling-icon" />
            </div>
          )}
          
          <div className="call-stats">
            <div className="stat">
              <PhoneOff size={16} className="stat-icon natc" />
              <span>NATC: {lead.calls_natc || 0}</span>
            </div>
            <div className="stat">
              <PhoneCall size={16} className="stat-icon connected" />
              <span>Connected: {lead.calls_c || 0}</span>
            </div>
          </div>
          
          <div className="dialog-actions">
            {!callInProgress ? (
              <>
                <button 
                  type="button"
                  className="btn-call-start"
                  onClick={onStartCall}
                  data-testid="start-call-btn"
                >
                  <Phone size={18} /> Start Call
                </button>
                <button 
                  type="button"
                  className="btn-cancel"
                  onClick={onClose}
                >
                  Cancel
                </button>
              </>
            ) : (
              <>
                <button 
                  type="button"
                  className="btn-call-end natc"
                  onClick={() => onEndCall('natc')}
                  data-testid="end-natc-btn"
                >
                  <PhoneOff size={18} /> Not Answered
                </button>
                <button 
                  type="button"
                  className="btn-call-end connected"
                  onClick={() => onEndCall('c')}
                  data-testid="end-connected-btn"
                >
                  <PhoneCall size={18} /> Connected
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
};

// My Demos Floating Popup Component
const MyDemosPopup = ({ onDialClick }) => {
  const [isExpanded, setIsExpanded] = useState(true); // Open by default
  const [demos, setDemos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('Today');

  useEffect(() => {
    fetchDemos();
  }, []);

  const fetchDemos = async () => {
    try {
      setLoading(true);
      await axios.post(`${API}/seed-demos`);
      const response = await axios.get(`${API}/demos`);
      setDemos(response.data);
    } catch (e) {
      console.error("Error fetching demos:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteDemo = async (demoId) => {
    try {
      await axios.delete(`${API}/demos/${demoId}`);
      setDemos(demos.filter(d => d.id !== demoId));
    } catch (e) {
      console.error("Error deleting demo:", e);
    }
  };

  const handleStatusChange = async (demo) => {
    try {
      const newStatus = demo.status === 'Pending' ? 'Completed' : 'Pending';
      await axios.put(`${API}/demos/${demo.id}`, { status: newStatus });
      setDemos(demos.map(d => d.id === demo.id ? { ...d, status: newStatus } : d));
    } catch (e) {
      console.error("Error updating demo status:", e);
    }
  };

  const filteredDemos = demos.filter(d => d.date_type === activeTab);

  return createPortal(
    <div className="my-demos-container" data-testid="my-demos-container">
      {/* Minimized Button */}
      {!isExpanded && (
        <button 
          className="my-demos-btn"
          onClick={() => setIsExpanded(true)}
          data-testid="my-demos-expand-btn"
        >
          <Calendar size={20} />
          <span>My Demos</span>
          <span className="demo-count">{demos.filter(d => d.status === 'Pending').length}</span>
        </button>
      )}

      {/* Expanded Popup */}
      {isExpanded && (
        <div className="my-demos-popup" data-testid="my-demos-popup">
          <div className="demos-popup-header">
            <div className="demos-header-left">
              <Calendar size={18} />
              <h3>My Demos</h3>
              <span className="demo-badge">{demos.filter(d => d.status === 'Pending').length} Pending</span>
            </div>
            <div className="demos-header-actions">
              <button 
                type="button" 
                className="demos-minimize-btn"
                onClick={() => setIsExpanded(false)}
                title="Minimize"
              >
                <Minus size={16} />
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className="demos-tabs">
            <label className="demos-tab-item">
              <input 
                type="checkbox" 
                checked={activeTab === 'Today'}
                onChange={() => setActiveTab('Today')}
              />
              <span>Today</span>
            </label>
            <label className="demos-tab-item">
              <input 
                type="checkbox" 
                checked={activeTab === 'Tomorrow'}
                onChange={() => setActiveTab('Tomorrow')}
              />
              <span>Tomorrow</span>
            </label>
          </div>

          {/* Table Header */}
          <div className="demos-table-header">
            <div className="demos-col time-col">Time Slot</div>
            <div className="demos-col action-col">Action</div>
            <div className="demos-col status-col">Status</div>
            <div className="demos-col close-col">X</div>
          </div>

          {/* Table Body */}
          <div className="demos-table-body">
            {loading ? (
              <div className="demos-loading">Loading demos...</div>
            ) : filteredDemos.length === 0 ? (
              <div className="demos-empty">No demos scheduled for {activeTab}</div>
            ) : (
              filteredDemos.map((demo) => (
                <div key={demo.id} className="demos-row" data-testid={`demo-row-${demo.id}`}>
                  <div className="demos-col time-col">
                    {demo.time_slot}
                  </div>
                  <div className="demos-col action-col">
                    <div className="demo-action-text">
                      <span className="demo-title">Demo At {demo.demo_time}</span>
                      <span className="demo-client">With {demo.client_name} {demo.company_name}</span>
                      <span className="demo-mobile">
                        Mob: {demo.mobile} 
                        <button 
                          type="button"
                          className="demo-dial-btn"
                          onClick={() => onDialClick(demo)}
                          data-testid={`demo-dial-${demo.id}`}
                        >
                          [Dial]
                        </button>
                      </span>
                    </div>
                  </div>
                  <div className="demos-col status-col">
                    <div className="demo-status-wrapper">
                      <span className={`demo-status ${demo.status.toLowerCase()}`}>
                        {demo.status}
                      </span>
                      <button 
                        type="button"
                        className="demo-call-icon"
                        onClick={() => onDialClick(demo)}
                        title="Call"
                      >
                        <Phone size={14} />
                      </button>
                    </div>
                  </div>
                  <div className="demos-col close-col">
                    <button 
                      type="button"
                      className="demo-delete-btn"
                      onClick={() => handleDeleteDemo(demo.id)}
                      title="Remove"
                    >
                      <X size={14} />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>,
    document.body
  );
};

const LeadManagement = () => {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
  const [dialingLead, setDialingLead] = useState(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [callInProgress, setCallInProgress] = useState(false);

  useEffect(() => {
    fetchLeads();
  }, []);

  const fetchLeads = async () => {
    try {
      setLoading(true);
      await axios.post(`${API}/seed`);
      const response = await axios.get(`${API}/leads`);
      setLeads(response.data);
    } catch (e) {
      console.error("Error fetching leads:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const sortedLeads = [...leads].sort((a, b) => {
    if (!sortConfig.key) return 0;
    const aVal = a[sortConfig.key];
    const bVal = b[sortConfig.key];
    if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
    if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
    return 0;
  });

  const openDialer = (lead) => {
    setDialingLead(lead);
    setIsDialogOpen(true);
    setCallInProgress(false);
  };

  const closeDialer = () => {
    setIsDialogOpen(false);
    setCallInProgress(false);
  };

  const handleStartCall = () => {
    setCallInProgress(true);
  };

  const handleEndCall = async (callType) => {
    if (!dialingLead) return;
    
    // Only log call if it's a lead (has lead_id format)
    if (dialingLead.id && !dialingLead.time_slot) {
      try {
        await axios.post(`${API}/calls`, {
          lead_id: dialingLead.id,
          call_type: callType,
          duration: 0,
          notes: ""
        });
        const response = await axios.get(`${API}/leads`);
        setLeads(response.data);
      } catch (e) {
        console.error("Error logging call:", e);
      }
    }
    
    closeDialer();
    setDialingLead(null);
  };

  const getPriorityColor = (priority) => {
    switch (priority?.toLowerCase()) {
      case 'hot': return 'bg-red-100 text-red-700';
      case 'warm': return 'bg-yellow-100 text-yellow-700';
      case 'cold': return 'bg-blue-100 text-blue-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const SortIcon = ({ column }) => {
    if (sortConfig.key !== column) {
      return <span className="sort-icon"><ChevronUp size={12} /><ChevronDown size={12} /></span>;
    }
    return sortConfig.direction === 'asc' 
      ? <ChevronUp size={14} className="sort-active" />
      : <ChevronDown size={14} className="sort-active" />;
  };

  return (
    <div className="lead-management" data-testid="lead-management">
      {/* Header */}
      <header className="header">
        <div className="header-left">
          <div className="logo">B</div>
          <h1>Lead Management</h1>
        </div>
        <div className="header-center">
          <div className="search-box">
            <Search size={18} />
            <input 
              type="text" 
              placeholder="Search by Mobile, GSTIN, Email, Lead ID"
              data-testid="search-input"
            />
            <Filter size={18} className="filter-icon" />
          </div>
        </div>
        <div className="header-right">
          <span>Switch to User</span>
          <div className="user-avatar">SK</div>
        </div>
      </header>

      {/* Tabs */}
      <div className="tabs-container">
        <div className="tabs-left">
          <button className="tab">Today</button>
          <button className="tab">All</button>
          <button className="tab active">Fresh Leads ({leads.length})</button>
          <button className="tab">New Leads</button>
          <button className="tab">Pending Follow Up</button>
          <button className="tab">Upcoming Follow Up</button>
          <button className="tab">Pending Demo</button>
          <button className="tab">Upcoming Demo</button>
        </div>
        <div className="tabs-right">
          <button className="btn-secondary">Bulk Assign</button>
          <button className="btn-primary">
            <Plus size={16} /> Create Lead
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="table-container">
        {loading ? (
          <div className="loading">Loading leads...</div>
        ) : (
          <table className="leads-table" data-testid="leads-table">
            <thead>
              <tr>
                <th onClick={() => handleSort('lead_name')} className="sortable">
                  <input type="checkbox" /> Lead Name <SortIcon column="lead_name" />
                </th>
                <th onClick={() => handleSort('partner_name')} className="sortable">
                  Partner Name <SortIcon column="partner_name" />
                </th>
                <th onClick={() => handleSort('next_follow_up_date')} className="sortable">
                  Next Follow Up <SortIcon column="next_follow_up_date" />
                </th>
                <th onClick={() => handleSort('calls_natc')} className="sortable calls-col" data-testid="calls-natc-header">
                  Calls NATC <SortIcon column="calls_natc" />
                </th>
                <th onClick={() => handleSort('calls_c')} className="sortable calls-col" data-testid="calls-c-header">
                  Calls -C <SortIcon column="calls_c" />
                </th>
                <th onClick={() => handleSort('type')} className="sortable">
                  Type <SortIcon column="type" />
                </th>
                <th onClick={() => handleSort('priority')} className="sortable">
                  Priority <SortIcon column="priority" />
                </th>
                <th onClick={() => handleSort('stage')} className="sortable">
                  Stage <SortIcon column="stage" />
                </th>
                <th onClick={() => handleSort('tat')} className="sortable">
                  TAT <SortIcon column="tat" />
                </th>
                <th>Mobile</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {sortedLeads.map((lead) => (
                <tr key={lead.id} data-testid={`lead-row-${lead.id}`}>
                  <td>
                    <input type="checkbox" />
                    <span className="lead-name">{lead.lead_name}</span>
                  </td>
                  <td className="partner-name">{lead.partner_name}</td>
                  <td className="follow-up">
                    {lead.next_follow_up_date} {lead.next_follow_up_time}
                  </td>
                  <td className="calls-natc" data-testid={`calls-natc-${lead.id}`}>
                    <span className={`call-count ${lead.calls_natc > 0 ? 'has-calls' : ''}`}>
                      {lead.calls_natc}
                    </span>
                  </td>
                  <td className="calls-c" data-testid={`calls-c-${lead.id}`}>
                    <span className={`call-count connected ${lead.calls_c > 0 ? 'has-calls' : ''}`}>
                      {lead.calls_c}
                    </span>
                  </td>
                  <td>{lead.type}</td>
                  <td>
                    <span className={`priority-badge ${getPriorityColor(lead.priority)}`}>
                      {lead.priority}
                    </span>
                  </td>
                  <td>
                    <span className="stage-badge">{lead.stage}</span>
                  </td>
                  <td>
                    <span className="tat-badge">{lead.tat}</span>
                  </td>
                  <td className="mobile">{lead.mobile}</td>
                  <td className="actions">
                    <button type="button" className="action-btn" title="Email">
                      <Mail size={16} />
                    </button>
                    <button 
                      type="button"
                      className="action-btn call-btn" 
                      title="Call"
                      onClick={() => openDialer(lead)}
                      data-testid={`call-btn-${lead.id}`}
                    >
                      <Phone size={16} />
                    </button>
                    <button type="button" className="action-btn" title="Schedule">
                      <Clock size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Shared Dialing Modal */}
      <DialingModal
        isOpen={isDialogOpen}
        lead={dialingLead}
        callInProgress={callInProgress}
        onClose={closeDialer}
        onStartCall={handleStartCall}
        onEndCall={handleEndCall}
      />

      {/* My Demos Floating Popup */}
      <MyDemosPopup onDialClick={openDialer} />
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <LeadManagement />
    </div>
  );
}

export default App;

/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState, useEffect } from 'react';
import { UserPlus, Search, RefreshCw, Mail, CheckCircle, Info, ExternalLink, AlertTriangle } from 'lucide-react';

export default function Outreach() {
  const [contacts, setContacts] = useState<any[]>([]);
  const [outreachLogs, setOutreachLogs] = useState<any[]>([]);
  const [jobs, setJobs] = useState<any[]>([]);

  // Manual Contact Form
  const [contactName, setContactName] = useState('');
  const [contactEmail, setContactEmail] = useState('');
  const [contactCompany, setContactCompany] = useState('');
  const [contactRole, setContactRole] = useState('');
  const [contactNotes, setContactNotes] = useState('');
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null);

  // Proxycurl search fields
  const [enrichCompany, setEnrichCompany] = useState('');
  const [enrichJobId, setEnrichJobId] = useState<number | null>(null);
  const [enriching, setEnriching] = useState(false);

  // States
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ text: '', type: '' });
  const [outreachConsent, setOutreachConsent] = useState(false);

  async function fetchData() {
    setLoading(true);
    try {
      const rContacts = await fetch('/api/contacts');
      const dContacts = await rContacts.json();
      setContacts(dContacts);

      const rLogs = await fetch('/api/outreach');
      const dLogs = await rLogs.json();
      setOutreachLogs(dLogs);

      const rJobs = await fetch('/api/jobs');
      const dJobs = await rJobs.json();
      setJobs(dJobs);
      if (dJobs.length > 0) {
        setSelectedJobId(dJobs[0].id);
        setEnrichJobId(dJobs[0].id);
      }
    } catch (e: any) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchData();
  }, []);

  const handleManualAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!contactName.trim() || !contactEmail.trim()) return;

    try {
      const r = await fetch('/api/contacts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: contactName,
          email: contactEmail,
          company: contactCompany,
          role: contactRole,
          source: 'Manual entry',
          notes: contactNotes,
          job_id: selectedJobId
        })
      });
      if (r.ok) {
        setMessage({ text: 'Contact created successfully!', type: 'success' });
        setContactName('');
        setContactEmail('');
        setContactCompany('');
        setContactRole('');
        setContactNotes('');
        fetchData();
      }
    } catch (e: any) {
      console.error(e);
    }
  };

  const handleProxycurlEnrich = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!enrichCompany.trim() || !enrichJobId) return;

    setEnriching(true);
    setMessage({ text: `Invoking Proxycurl API to crawl employees of '${enrichCompany}' on LinkedIn...`, type: 'info' });
    try {
      const r = await fetch('/api/contacts/enrich', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_name: enrichCompany,
          job_id: enrichJobId
        })
      });
      const data = await r.json();
      if (r.ok) {
        if (data.contacts && data.contacts.length > 0) {
          setMessage({ text: `Proxycurl successfully resolved company and imported ${data.contacts.length} recruiter contacts!`, type: 'success' });
        } else {
          setMessage({ text: 'Proxycurl completed but found no recruiters matching keyword filter.', type: 'warning' });
        }
        setEnrichCompany('');
        fetchData();
      } else {
        setMessage({ text: data.detail || 'Proxycurl enrichment failed.', type: 'error' });
      }
    } catch (err: any) {
      setMessage({ text: `Error: ${err.message}`, type: 'error' });
    } finally {
      setEnriching(false);
    }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/10 pb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-2">
            <Mail className="text-indigo-400" size={28} />
            Recruiter Outreach & Networking
          </h1>
          <p className="text-gray-400 mt-1">Look up and record recruiter contact info, and view follow-up message logs.</p>
        </div>
        <button onClick={fetchData} disabled={loading}
          className="flex items-center gap-2 surface-panel hover:bg-white/10 text-gray-300 font-medium px-4 py-2.5 rounded-xl text-sm transition-all active:scale-95">
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          Refresh Lists
        </button>
      </div>

      {/* Notifications */}
      {message.text && (
        <div className={`p-4 rounded-xl flex items-center gap-3 border ${
          message.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300' :
          message.type === 'error' ? 'bg-rose-500/10 border-rose-500/30 text-rose-300' :
          message.type === 'warning' ? 'bg-amber-500/10 border-amber-500/30 text-amber-300' :
          'bg-indigo-500/10 border-indigo-500/30 text-indigo-300'
        }`}>
          {message.type === 'success' ? <CheckCircle size={20} /> : <Info size={20} />}
          <span className="text-sm font-medium">{message.text}</span>
        </div>
      )}

      {/* CAN-SPAM & GDPR Compliance Card */}
      <div className="bg-amber-500/10 border border-amber-500/20 text-amber-300 rounded-2xl p-6 backdrop-blur-xl space-y-4">
        <div className="flex items-center gap-2 font-bold text-base">
          <AlertTriangle size={20} className="text-amber-400" />
          Recruiter Outreach Compliance Notice (CAN-SPAM & GDPR)
        </div>
        <p className="text-xs text-amber-200/90 leading-relaxed">
          When sending cold outreach emails to recruiters, you must comply with anti-spam and privacy regulations:
        </p>
        <ul className="list-disc pl-5 text-xs text-gray-300 space-y-1.5 leading-normal">
          <li><strong>CAN-SPAM Act:</strong> You must include a valid physical mailing address in your email footer, identify the email as an advertisement if applicable, and provide a clear way to opt out of future messages.</li>
          <li><strong>GDPR (Europe):</strong> If contacting individuals in the EU, you must have a lawful basis for processing their personal data (e.g. legitimate interest or consent) and respect their right to be forgotten (delete their data on request).</li>
          <li><strong>Opt-Out Tracking:</strong> Keep track of recruiters who ask not to be contacted and ensure they are immediately removed from your database.</li>
        </ul>
        <label className="flex items-start gap-2.5 cursor-pointer pt-2 select-none">
          <input 
            type="checkbox" 
            checked={outreachConsent} 
            onChange={(e) => setOutreachConsent(e.target.checked)} 
            className="mt-0.5 rounded border-white/10 bg-neutral-900 text-indigo-500 focus:ring-0 focus:ring-offset-0" 
          />
          <span className="text-xs text-gray-300 font-semibold">
            I confirm that my outreach templates include required compliance headers/footers (physical address & opt-out link) and that I will comply with local privacy laws.
          </span>
        </label>
      </div>

      {/* Top forms: Manual Entry and Proxycurl search */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Proxycurl Recruiter Finder */}
        <div className="surface-panel p-6 rounded-2xl space-y-4">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Search className="text-indigo-400" size={20} />
            Automated Recruiter Lookup (Proxycurl API)
          </h2>
          <p className="text-sm text-gray-400">
            Enter a company name. Proxycurl will automatically resolve its LinkedIn URL and find contacts with keywords (e.g. Recruiter, Talent Partner).
          </p>

          <form onSubmit={handleProxycurlEnrich} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Company Name</label>
                <input type="text" required value={enrichCompany} onChange={(e) => setEnrichCompany(e.target.value)}
                  className="w-full surface-panel rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500 text-sm transition-all" 
                  placeholder="e.g. Canonical or Google" />
              </div>
              
              <div className="col-span-2">
                <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Associate with Saved Job</label>
                <select value={enrichJobId || ''} onChange={(e) => setEnrichJobId(parseInt(e.target.value))}
                  className="w-full bg-neutral-900 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500 text-sm transition-all">
                  {jobs.map(j => (
                    <option key={j.id} value={j.id}>
                      {j.company} — {j.title}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <button type="submit" disabled={enriching || !outreachConsent}
              className="btn-primary font-semibold rounded-xl px-6 py-3.5 text-xs transition-all active:scale-95 disabled:opacity-50 flex items-center justify-center gap-2">
              {enriching ? <RefreshCw className="animate-spin" size={14} /> : null}
              Find Recruiters via Proxycurl
            </button>
          </form>
        </div>

        {/* Manual Contact Entry */}
        <div className="surface-panel p-6 rounded-2xl space-y-4">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <UserPlus className="text-indigo-400" size={20} />
            Log Contact Manually
          </h2>
          <p className="text-sm text-gray-400">Record info about a recruiter, referrer, or interviewer you spoke with.</p>

          <form onSubmit={handleManualAdd} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1">Contact Name</label>
                <input type="text" required value={contactName} onChange={(e) => setContactName(e.target.value)}
                  className="w-full surface-panel rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500 text-xs transition-all" placeholder="Jane Smith" />
              </div>
              
              <div>
                <label className="block text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1">Email Address</label>
                <input type="email" required value={contactEmail} onChange={(e) => setContactEmail(e.target.value)}
                  className="w-full surface-panel rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500 text-xs transition-all" placeholder="jane@company.com" />
              </div>

              <div>
                <label className="block text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1">Company</label>
                <input type="text" value={contactCompany} onChange={(e) => setContactCompany(e.target.value)}
                  className="w-full surface-panel rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500 text-xs transition-all" placeholder="Canonical" />
              </div>

              <div>
                <label className="block text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1">Role / Job Title</label>
                <input type="text" value={contactRole} onChange={(e) => setContactRole(e.target.value)}
                  className="w-full surface-panel rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500 text-xs transition-all" placeholder="Technical Recruiter" />
              </div>

              <div className="col-span-2">
                <label className="block text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1">Linked Job Linkage</label>
                <select value={selectedJobId || ''} onChange={(e) => setSelectedJobId(parseInt(e.target.value))}
                  className="w-full bg-neutral-900 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500 text-xs transition-all">
                  {jobs.map(j => (
                    <option key={j.id} value={j.id}>
                      {j.company} — {j.title}
                    </option>
                  ))}
                </select>
              </div>

              <div className="col-span-2">
                <label className="block text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1">Notes</label>
                <input type="text" value={contactNotes} onChange={(e) => setContactNotes(e.target.value)}
                  className="w-full surface-panel rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500 text-xs transition-all" placeholder="Spoke with them on LinkedIn..." />
              </div>
            </div>

            <button type="submit" disabled={!outreachConsent}
              className="w-full bg-white/5 hover:bg-white/10 border border-white/10 text-white font-semibold rounded-xl py-2.5 text-xs transition-all active:scale-95 disabled:opacity-50 disabled:hover:bg-white/5 mt-1">
              Add Contact
            </button>
          </form>
        </div>
      </div>

      {/* Lists Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recruiters List (takes 2 cols) */}
        <div className="lg:col-span-2 surface-panel p-6 rounded-2xl space-y-4">
          <h3 className="text-md font-semibold text-white">Contacts & Recruiter Database</h3>
          
          <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
            {contacts.length === 0 ? (
              <div className="text-xs text-gray-500 py-8 text-center">No contacts saved yet.</div>
            ) : (
              contacts.map(c => {
                const isPlaceholderEmail = c.email.includes('@example.com') && c.email.startsWith('recruiter-');
                
                return (
                  <div key={c.id} className="border border-white/5 bg-white/[0.01] rounded-xl p-4 flex justify-between items-start gap-4">
                    <div className="space-y-1">
                      <h4 className="text-sm font-bold text-white leading-snug">{c.name}</h4>
                      <p className="text-xs text-gray-400">
                        <span className="font-semibold text-indigo-300">{c.role}</span>
                        {c.company ? ` @ ${c.company}` : ''}
                      </p>
                      
                      {c.notes && (
                        <p className="text-[11px] text-gray-500 italic mt-1 leading-normal max-w-sm truncate">
                          {c.notes}
                        </p>
                      )}
                      
                      <div className="flex gap-2 pt-2 text-[10px] text-gray-400">
                        <span>Source: <strong>{c.source}</strong></span>
                      </div>
                    </div>
                    
                    <div className="flex gap-2">
                      {!isPlaceholderEmail && (
                        <a href={`mailto:${c.email}`} className="p-2 bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 rounded-lg text-xs font-semibold flex items-center gap-1 transition-all">
                          <Mail size={14} /> Email
                        </a>
                      )}
                      {c.notes?.includes('http') && (
                        <a href={c.notes.match(/https?:\/\/[^\s]+/)?.[0]} target="_blank" rel="noopener noreferrer"
                          className="p-2 bg-white/5 hover:bg-white/10 text-gray-300 rounded-lg text-xs font-semibold flex items-center gap-1 transition-all">
                          Profile <ExternalLink size={12} />
                        </a>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Outreach History Log */}
        <div className="lg:col-span-1 surface-panel p-6 rounded-2xl space-y-4">
          <h3 className="text-md font-semibold text-white">Outreach Logs</h3>
          
          <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
            {outreachLogs.length === 0 ? (
              <div className="text-xs text-gray-500 py-8 text-center">No outreach logs recorded yet.</div>
            ) : (
              outreachLogs.map(l => (
                <div key={l.id} className="border border-white/5 bg-white/[0.01] rounded-xl p-4 space-y-2">
                  <div className="flex justify-between items-start">
                    <span className="text-[9px] font-bold bg-emerald-500/20 text-emerald-300 px-1.5 py-0.5 rounded uppercase shrink-0">Sent</span>
                    <span className="text-[9px] text-gray-500 font-semibold">{l.created_at?.split('T')[0]}</span>
                  </div>
                  
                  <div className="text-xs">
                    <div className="text-white font-semibold truncate">Subject: {l.subject}</div>
                    <div className="text-indigo-300 font-medium text-[10px] mt-0.5">Recruiter: {l.contact_name || l.contact_email || 'Unlinked Recruiter'}</div>
                  </div>
                  
                  <pre className="text-[10px] text-gray-400 font-mono bg-black/15 p-2 rounded max-h-24 overflow-y-auto whitespace-pre-wrap leading-normal border border-white/5">
                    {l.body}
                  </pre>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

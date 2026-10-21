import React from 'react';
import { AlertTriangle, CheckCircle2, HelpCircle, ShieldAlert } from 'lucide-react';
import { Prospect } from '../../types';

interface EvidenceTrustPanelProps {
  prospect: Prospect;
}

type Tone = 'good' | 'warn' | 'bad' | 'neutral';

const TONE_CLASS: Record<Tone, string> = {
  good: 'bg-[#18261F] text-[#80B89A] border-[#253D30]',
  warn: 'bg-[#2A2418] text-[#D8B779] border-[#4A3E22]',
  bad: 'bg-[#321A1A] text-[#D78383] border-[#522525]',
  neutral: 'bg-[#1A1C20] text-[#A0A5AD] border-[#2B2F36]',
};

const IDENTITY_LABEL: Record<string, { label: string; tone: Tone }> = {
  verified: { label: 'Verified', tone: 'good' },
  likely_match: { label: 'Likely match (not independently verified)', tone: 'warn' },
  uncertain: { label: 'Uncertain', tone: 'warn' },
  conflicting: { label: 'Conflicting', tone: 'bad' },
  not_found: { label: 'No website discovered (absence not confirmed)', tone: 'neutral' },
  not_checked: { label: 'Not checked', tone: 'neutral' },
};

const CONTACT_LABEL: Record<string, { label: string; tone: Tone }> = {
  official_source: { label: 'From business website', tone: 'good' },
  corroborated: { label: 'Corroborated by multiple sources', tone: 'good' },
  provider_verified: { label: 'Provider-scored (ownership unconfirmed)', tone: 'warn' },
  third_party_candidate: { label: 'Third-party candidate', tone: 'warn' },
  unverified: { label: 'Unverified', tone: 'warn' },
  conflicting: { label: 'Conflicting – likely not the business', tone: 'bad' },
  none: { label: 'No email recorded', tone: 'neutral' },
};

const SOCIAL_LABEL: Record<string, { label: string; tone: Tone }> = {
  reciprocal_match: { label: 'Reciprocal link confirmed', tone: 'good' },
  strong_match: { label: 'Strong match', tone: 'good' },
  uncertain_match: { label: 'Uncertain – unconfirmed', tone: 'warn' },
  incorrect_match: { label: 'Likely wrong account', tone: 'bad' },
  not_found: { label: 'Not found (search is not proof of absence)', tone: 'neutral' },
};

const Pill: React.FC<{ tone: Tone; children: React.ReactNode }> = ({ tone, children }) => (
  <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono border ${TONE_CLASS[tone]}`}>{children}</span>
);

const fmt = (iso?: string) => {
  if (!iso) return 'unknown';
  const d = new Date(iso);
  return isNaN(d.getTime()) ? iso : d.toLocaleString();
};

export const EvidenceTrustPanel: React.FC<EvidenceTrustPanelProps> = ({ prospect }) => {
  const identityKey = (prospect.identityStatus as string) || 'not_checked';
  const identity = IDENTITY_LABEL[identityKey] || IDENTITY_LABEL.not_checked;
  const ev = prospect.identityEvidence || null;
  const prov = prospect.contactProvenance && prospect.contactProvenance.email ? prospect.contactProvenance : null;
  const contactKey = prov?.status || (prospect.email ? 'unverified' : 'none');
  const contact = CONTACT_LABEL[contactKey] || CONTACT_LABEL.unverified;
  const socials = Object.values(prospect.socialProfiles || {}).filter(Boolean);
  const websiteWithheld = identityKey === 'conflicting' || identityKey === 'uncertain';
  const limitations = prospect.scoring?.limitations || [];

  return (
    <div className="rounded border border-[#2B2F36] bg-[#141618] p-3.5 flex flex-col gap-2.5" data-testid="evidence-trust-panel">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-medium text-[#727780] uppercase tracking-wider">
          Evidence &amp; Trust
        </span>
        {websiteWithheld && (
          <span className="inline-flex items-center gap-1 text-[10px] text-[#D78383]">
            <ShieldAlert className="w-3 h-3" /> Website-specific outreach on hold
          </span>
        )}
      </div>

      {/* Identity */}
      <div className="flex flex-col gap-1">
        <div className="flex items-center justify-between">
          <span className="text-[#A0A5AD]">Business ↔ website identity</span>
          <Pill tone={identity.tone}>{identity.label}</Pill>
        </div>
        {websiteWithheld && (
          <div className="flex items-start gap-1.5 text-[11px] text-[#D8B779]">
            <AlertTriangle className="w-3 h-3 mt-0.5 shrink-0" />
            <span>
              This domain is not confirmed as the business&apos;s own site. Audit findings and website-specific
              recommendations are excluded from the score and from AI drafts until you confirm it.
            </span>
          </div>
        )}
        {ev && (ev.reasons?.length || ev.conflicting_domains?.length) ? (
          <details className="text-[11px] text-[#A0A5AD]">
            <summary className="cursor-pointer text-[#727780] hover:text-[#A0A5AD]">Why? (evidence)</summary>
            <ul className="list-disc ml-4 mt-1 flex flex-col gap-0.5">
              {(ev.reasons || []).map((r, i) => <li key={i}>{r}</li>)}
              {ev.verified_at && <li>Checked {fmt(ev.verified_at)}</li>}
              {ev.operator_override && (
                <li>
                  Operator set status to “{ev.operator_override.status}” on {fmt(ev.operator_override.at)}
                  {ev.operator_override.previous_status ? ` (was ${ev.operator_override.previous_status})` : ''}
                </li>
              )}
            </ul>
          </details>
        ) : null}
      </div>

      {/* Contact */}
      <div className="flex flex-col gap-1 pt-2 border-t border-[#22252A]">
        <div className="flex items-center justify-between">
          <span className="text-[#A0A5AD]">Email source &amp; trust</span>
          <Pill tone={contact.tone}>{contact.label}</Pill>
        </div>
        {prov && (
          <details className="text-[11px] text-[#A0A5AD]">
            <summary className="cursor-pointer text-[#727780] hover:text-[#A0A5AD]">Evidence</summary>
            <ul className="list-disc ml-4 mt-1 flex flex-col gap-0.5">
              <li>Source: {prov.source_type || 'unknown'} via {prov.source_provider || 'unknown'}</li>
              {prov.source_url && <li className="break-all">Reference: {prov.source_url}</li>}
              <li>Domain has mail (MX) records: {prov.mx_verified ? 'yes' : 'no'} — this does not confirm the mailbox exists</li>
              <li>Mailbox confirmed: {prov.mailbox_confirmed ? 'yes' : 'no'}</li>
              {prov.rationale && <li>{prov.rationale}</li>}
              {prov.discovered_at && <li>Discovered {fmt(prov.discovered_at)}</li>}
            </ul>
          </details>
        )}
        {!prov && prospect.email && (
          <span className="text-[11px] text-[#727780]">
            No provenance recorded for this address (imported or added manually). Treat as unverified.
          </span>
        )}
      </div>

      {/* Social */}
      <div className="flex flex-col gap-1 pt-2 border-t border-[#22252A]">
        <span className="text-[#A0A5AD]">Social profiles</span>
        {socials.length === 0 ? (
          <span className="text-[11px] text-[#727780] inline-flex items-center gap-1">
            <HelpCircle className="w-3 h-3" /> None matched yet. Run Deep Search; a failed search does not prove no profile exists.
          </span>
        ) : (
          socials.map((s, i) => {
            const meta = SOCIAL_LABEL[s.match_status || ''] || { label: s.match_status || 'unknown', tone: 'neutral' as Tone };
            const confirmed = s.match_status === 'reciprocal_match' || s.match_status === 'strong_match';
            return (
              <div key={i} className="flex flex-col gap-0.5 text-[11px]">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-[#F3F4F6] capitalize flex items-center gap-1">
                    {confirmed && <CheckCircle2 className="w-3 h-3 text-[#80B89A]" />}
                    {s.platform}
                    {s.url && (
                      <a href={s.url} target="_blank" rel="noopener noreferrer" className="text-[#D8E7A2] hover:underline break-all normal-case">
                        {s.url.replace(/https?:\/\/(www\.)?/, '')}
                      </a>
                    )}
                  </span>
                  <Pill tone={meta.tone}>{meta.label}</Pill>
                </div>
                <details className="text-[#A0A5AD]">
                  <summary className="cursor-pointer text-[#727780] hover:text-[#A0A5AD]">Evidence</summary>
                  <ul className="list-disc ml-4 mt-1 flex flex-col gap-0.5">
                    {s.evidence && <li>{s.evidence}</li>}
                    {s.contradictory_info && <li className="text-[#D8B779]">Contradicting: {s.contradictory_info}</li>}
                    <li>Last checked {fmt(s.last_checked)}</li>
                  </ul>
                </details>
              </div>
            );
          })
        )}
      </div>

      {/* Score limitations */}
      {limitations.length > 0 && (
        <details className="pt-2 border-t border-[#22252A] text-[11px] text-[#A0A5AD]">
          <summary className="cursor-pointer text-[#727780] hover:text-[#A0A5AD]">
            Reasons for uncertainty ({limitations.length})
          </summary>
          <ul className="list-disc ml-4 mt-1 flex flex-col gap-0.5">
            {limitations.map((l, i) => <li key={i}>{l}</li>)}
          </ul>
        </details>
      )}
    </div>
  );
};

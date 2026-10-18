import React from 'react';
import { SeverityLevel, WebsiteCondition, ProspectStatus } from '../../types';

interface BadgeProps {
  children?: React.ReactNode;
  variant?: 'severity' | 'website' | 'status' | 'neutral' | 'accent';
  severity?: SeverityLevel;
  websiteStatus?: WebsiteCondition;
  prospectStatus?: ProspectStatus;
  size?: 'sm' | 'md';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  severity,
  websiteStatus,
  prospectStatus,
  size = 'sm',
  className = '',
}) => {
  const sizeClasses = size === 'sm' ? 'text-[11px] px-2 py-0.5' : 'text-[12px] px-2.5 py-1';

  if (variant === 'severity' || severity) {
    const sev = severity || 'info';
    const config = {
      high: {
        bg: 'bg-[#2A1818]',
        text: 'text-[#D78383]',
        border: 'border-[#4A2626]',
        label: 'High',
      },
      medium: {
        bg: 'bg-[#2A2417]',
        text: 'text-[#D8B16C]',
        border: 'border-[#4A3D22]',
        label: 'Medium',
      },
      low: {
        bg: 'bg-[#18261F]',
        text: 'text-[#80B89A]',
        border: 'border-[#253E31]',
        label: 'Low',
      },
      info: {
        bg: 'bg-[#17222B]',
        text: 'text-[#91B7D8]',
        border: 'border-[#223545]',
        label: 'Info',
      },
    }[sev] || {
      bg: 'bg-[#17222B]',
      text: 'text-[#91B7D8]',
      border: 'border-[#223545]',
      label: sev,
    };

    return (
      <span
        className={`inline-flex items-center font-mono font-medium rounded border ${config.bg} ${config.text} ${config.border} ${sizeClasses} ${className}`}
      >
        {children || config.label}
      </span>
    );
  }

  if (variant === 'website' || websiteStatus) {
    const ws = websiteStatus || 'active';
    const config = {
      active: {
        bg: 'bg-[#18261F]',
        text: 'text-[#80B89A]',
        border: 'border-[#253E31]',
        dot: 'bg-[#80B89A]',
        label: 'Active',
      },
      not_listed: {
        bg: 'bg-[#212328]',
        text: 'text-[#A0A5AD]',
        border: 'border-[#30343A]',
        dot: 'bg-[#727780]',
        label: 'Not listed',
      },
      unreachable: {
        bg: 'bg-[#2A1818]',
        text: 'text-[#D78383]',
        border: 'border-[#4A2626]',
        dot: 'bg-[#D78383]',
        label: 'Unreachable',
      },
      dns_error: {
        bg: 'bg-[#2A2417]',
        text: 'text-[#D8B16C]',
        border: 'border-[#4A3D22]',
        dot: 'bg-[#D8B16C]',
        label: 'DNS Issue',
      },
      ssl_expired: {
        bg: 'bg-[#2A1818]',
        text: 'text-[#D78383]',
        border: 'border-[#4A2626]',
        dot: 'bg-[#D78383]',
        label: 'SSL Expired',
      },
      broken_pages: {
        bg: 'bg-[#2A2417]',
        text: 'text-[#D8B16C]',
        border: 'border-[#4A3D22]',
        dot: 'bg-[#D8B16C]',
        label: 'Broken routes',
      },
      verification_required: {
        bg: 'bg-[#2A2417]',
        text: 'text-[#D8B16C]',
        border: 'border-[#4A3D22]',
        dot: 'bg-[#D8B16C]',
        label: 'Verification required',
      },
      verified_accessible: {
        bg: 'bg-[#18261F]',
        text: 'text-[#80B89A]',
        border: 'border-[#253E31]',
        dot: 'bg-[#80B89A]',
        label: 'Verified accessible',
      },
      verification_failed: {
        bg: 'bg-[#2A1818]',
        text: 'text-[#D78383]',
        border: 'border-[#4A2626]',
        dot: 'bg-[#D78383]',
        label: 'Verification failed',
      },
    }[ws] || {
      bg: 'bg-[#212328]',
      text: 'text-[#A0A5AD]',
      border: 'border-[#30343A]',
      dot: 'bg-[#727780]',
      label: ws,
    };

    return (
      <span
        className={`inline-flex items-center gap-1.5 font-medium rounded border ${config.bg} ${config.text} ${config.border} ${sizeClasses} ${className}`}
      >
        <span className={`w-1.5 h-1.5 rounded-full ${config.dot}`} />
        {children || config.label}
      </span>
    );
  }

  if (variant === 'status' || prospectStatus) {
    const ps = prospectStatus || 'new';
    const config = {
      new: {
        bg: 'bg-[#1C2026]',
        text: 'text-[#91B7D8]',
        border: 'border-[#29323D]',
        label: 'New',
      },
      needs_audit: {
        bg: 'bg-[#28251C]',
        text: 'text-[#D8B16C]',
        border: 'border-[#423C2B]',
        label: 'Needs audit',
      },
      needs_review: {
        bg: 'bg-[#24261C]',
        text: 'text-[#D8E7A2]',
        border: 'border-[#3D4428]',
        label: 'Needs review',
      },
      draft_ready: {
        bg: 'bg-[#1A2622]',
        text: 'text-[#80B89A]',
        border: 'border-[#284236]',
        label: 'Draft ready',
      },
      contacted: {
        bg: 'bg-[#212328]',
        text: 'text-[#A0A5AD]',
        border: 'border-[#30343A]',
        label: 'Contacted',
      },
      approved: {
        bg: 'bg-[#18261F]',
        text: 'text-[#80B89A]',
        border: 'border-[#253E31]',
        label: 'Approved',
      },
      archived: {
        bg: 'bg-[#18191C]',
        text: 'text-[#727780]',
        border: 'border-[#26292E]',
        label: 'Archived',
      },
    }[ps] || {
      bg: 'bg-[#1C2026]',
      text: 'text-[#91B7D8]',
      border: 'border-[#29323D]',
      label: ps,
    };

    return (
      <span
        className={`inline-flex items-center font-medium rounded border ${config.bg} ${config.text} ${config.border} ${sizeClasses} ${className}`}
      >
        {children || config.label}
      </span>
    );
  }

  if (variant === 'accent') {
    return (
      <span
        className={`inline-flex items-center font-mono font-medium rounded border bg-[#23281B] text-[#D8E7A2] border-[#3E4829] ${sizeClasses} ${className}`}
      >
        {children}
      </span>
    );
  }

  return (
    <span
      className={`inline-flex items-center font-medium rounded border bg-[#1D2024] text-[#A0A5AD] border-[#30343A] ${sizeClasses} ${className}`}
    >
      {children}
    </span>
  );
};

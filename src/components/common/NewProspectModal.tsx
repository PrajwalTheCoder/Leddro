import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { Button } from './Button';
import { X, Building2, Globe, MapPin, Tag } from 'lucide-react';

interface NewProspectModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const NewProspectModal: React.FC<NewProspectModalProps> = ({ isOpen, onClose }) => {
  const { addProspect } = useApp();
  const [name, setName] = useState('');
  const [category, setCategory] = useState('');
  const [city, setCity] = useState('');
  const [state, setState] = useState('Maharashtra');
  const [country, setCountry] = useState('India');
  const [websiteUrl, setWebsiteUrl] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [notes, setNotes] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    const trimmedUrl = websiteUrl.trim();
    addProspect({
      name: name.trim(),
      category: category.trim() || 'Commercial Services',
      location: {
        city: city.trim() || 'Navi Mumbai',
        state: state.trim() || 'Maharashtra',
        country: country.trim() || 'India',
      },
      websiteUrl: trimmedUrl.length > 0 ? trimmedUrl : undefined,
      websiteStatus: trimmedUrl.length > 0 ? 'active' : 'not_listed',
      opportunityScore: trimmedUrl.length > 0 ? 75 : 88,
      scoreBreakdown: {
        technicalUrgency: 25,
        commercialIntent: 25,
        resolutionEase: 25,
      },
      status: 'new',
      phone: phone.trim() || undefined,
      email: email.trim() || undefined,
      tags: ['Manual Add'],
      recommendedAction: trimmedUrl.length > 0 ? 'Run initial website audit.' : 'Verify telephone and commercial listing.',
      notes: notes.trim() || undefined,
    });

    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4">
      <div 
        className="w-full max-w-lg rounded border border-[#30343A] bg-[#17191C] shadow-2xl overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-[#24272D]">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded bg-[#1D2024] border border-[#30343A]">
              <Building2 className="w-4 h-4 text-[#D8E7A2]" />
            </div>
            <div>
              <h3 className="text-[14px] font-medium text-[#F3F4F6]">Add Single Prospect</h3>
              <p className="text-[12px] text-[#727780]">Register a business target into your research pipeline</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-[#727780] hover:text-[#F3F4F6] hover:bg-[#202328]"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 flex flex-col gap-3.5 max-h-[75vh] overflow-y-auto">
          <div>
            <label className="block text-[12px] font-medium text-[#A0A5AD] mb-1">Business Name *</label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Skyline Architecture Studio"
              className="w-full bg-[#111214] border border-[#30343A] rounded px-3 py-1.5 text-[13px] text-[#F3F4F6] placeholder-[#575C66] focus:border-[#4B5361] outline-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[12px] font-medium text-[#A0A5AD] mb-1">Business Category</label>
              <input
                type="text"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                placeholder="e.g. Interior design, Manufacturing"
                className="w-full bg-[#111214] border border-[#30343A] rounded px-3 py-1.5 text-[13px] text-[#F3F4F6] placeholder-[#575C66] focus:border-[#4B5361] outline-none"
              />
            </div>
            <div>
              <label className="block text-[12px] font-medium text-[#A0A5AD] mb-1">City</label>
              <input
                type="text"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                placeholder="e.g. Navi Mumbai"
                className="w-full bg-[#111214] border border-[#30343A] rounded px-3 py-1.5 text-[13px] text-[#F3F4F6] placeholder-[#575C66] focus:border-[#4B5361] outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-[12px] font-medium text-[#A0A5AD] mb-1">
              Website URL (Leave blank if unlisted)
            </label>
            <div className="relative">
              <Globe className="w-4 h-4 text-[#727780] absolute left-3 top-2.5" />
              <input
                type="text"
                value={websiteUrl}
                onChange={(e) => setWebsiteUrl(e.target.value)}
                placeholder="https://example.com"
                className="w-full bg-[#111214] border border-[#30343A] rounded pl-9 pr-3 py-1.5 text-[13px] font-mono text-[#F3F4F6] placeholder-[#575C66] focus:border-[#4B5361] outline-none"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[12px] font-medium text-[#A0A5AD] mb-1">Direct Email (optional)</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="contact@business.com"
                className="w-full bg-[#111214] border border-[#30343A] rounded px-3 py-1.5 text-[13px] text-[#F3F4F6] placeholder-[#575C66] focus:border-[#4B5361] outline-none"
              />
            </div>
            <div>
              <label className="block text-[12px] font-medium text-[#A0A5AD] mb-1">Phone Number (optional)</label>
              <input
                type="text"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+91 22 2840 0000"
                className="w-full bg-[#111214] border border-[#30343A] rounded px-3 py-1.5 text-[13px] text-[#F3F4F6] placeholder-[#575C66] focus:border-[#4B5361] outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-[12px] font-medium text-[#A0A5AD] mb-1">Operational Notes</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
              placeholder="Key observations or context about this prospect..."
              className="w-full bg-[#111214] border border-[#30343A] rounded p-2.5 text-[12px] text-[#F3F4F6] placeholder-[#575C66] focus:border-[#4B5361] outline-none"
            />
          </div>

          <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-[#24272D] mt-2">
            <Button variant="ghost" size="md" type="button" onClick={onClose}>
              Cancel
            </Button>
            <Button variant="primary" size="md" type="submit">
              Save Prospect
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

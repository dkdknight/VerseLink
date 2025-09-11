import React, { useState } from 'react';
import { DocumentDuplicateIcon, CheckIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

const CopyButton = ({ text }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      toast.success('ID copié !');
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      toast.error("Impossible de copier l'ID");
    }
  };

  return (
    <button
      type="button"
      onClick={handleCopy}
      className="btn-ghost flex items-center text-sm"
    >
      {copied ? (
        <>
          <CheckIcon className="w-4 h-4 mr-1" />
          Copié !
        </>
      ) : (
        <>
          <DocumentDuplicateIcon className="w-4 h-4 mr-1" />
          Copier
        </>
      )}
    </button>
  );
};

export default CopyButton;
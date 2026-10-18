import React from 'react';
import { Loader2 } from 'lucide-react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'accent-subtle';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'secondary',
  size = 'md',
  isLoading = false,
  leftIcon,
  rightIcon,
  className = '',
  disabled,
  ...props
}) => {
  const baseStyles = 'inline-flex items-center justify-center font-medium rounded transition-colors focus:outline-none focus:ring-1 focus:ring-[#D8E7A2] disabled:opacity-50 disabled:cursor-not-allowed select-none whitespace-nowrap';

  const sizeStyles = {
    sm: 'text-[12px] h-7 px-2.5 gap-1.5',
    md: 'text-[13px] h-8 px-3 gap-2',
    lg: 'text-[14px] h-9 px-4 gap-2',
  }[size];

  const variantStyles = {
    primary: 'bg-[#D8E7A2] text-[#111214] font-semibold hover:bg-[#C7D791] active:bg-[#B6C580] border border-[#B5C77A]',
    secondary: 'bg-[#1D2024] text-[#F3F4F6] border border-[#30343A] hover:bg-[#24272C] hover:border-[#3E434B] active:bg-[#1A1D20]',
    ghost: 'bg-transparent text-[#A0A5AD] hover:bg-[#1D2024] hover:text-[#F3F4F6] border border-transparent',
    danger: 'bg-[#2A1818] text-[#D78383] border border-[#4A2626] hover:bg-[#341E1E]',
    'accent-subtle': 'bg-[#21261B] text-[#D8E7A2] border border-[#3D4728] hover:bg-[#282F20]'
  }[variant];

  return (
    <button
      className={`${baseStyles} ${sizeStyles} ${variantStyles} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <Loader2 className="w-3.5 h-3.5 animate-spin" />
      ) : (
        leftIcon
      )}
      {children}
      {!isLoading && rightIcon}
    </button>
  );
};

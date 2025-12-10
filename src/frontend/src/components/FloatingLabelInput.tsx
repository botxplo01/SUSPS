/** @author: David Lameck **/

import type { InputHTMLAttributes } from "react";

interface FloatingLabelInputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  id: string;
}

export function FloatingLabelInput({ label, id, type = "text", ...rest }: FloatingLabelInputProps) {
  return (
    <div className="relative mt-6">
      <input
        id={id}
        type={type}
        className="peer block w-full border-b border-gray-400 bg-transparent px-0 pb-1 pt-4 text-sm text-gray-900 placeholder-transparent focus:border-emerald-500 focus:outline-none"
        placeholder=" "
        {...rest}
      />
      <label
        htmlFor={id}
        className="pointer-events-none absolute left-0 top-0 text-xs text-gray-500 transition-all peer-placeholder-shown:top-4 peer-placeholder-shown:text-base peer-placeholder-shown:text-gray-400 peer-focus:text-emerald-600"
      >
        {label}
      </label>
    </div>
  );
}

"use client";

import * as React from "react";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import {
  FormField,
  FormControl,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Slider } from "@/components/ui/slider";
import { ConfigurationFormFieldProps } from "@/components/configuration-form";
import { Input } from "@/components/ui/input";
import { z } from "zod";
import { ConfigurationFormSchema } from "./configuration-form";

const getMinMaxForField = (schema: z.ZodNumber) => {
  const minCheck = schema._def.checks.find((check) => check.kind === "min");
  const maxCheck = schema._def.checks.find((check) => check.kind === "max");

  return {
    minValue: minCheck ? minCheck.value : undefined,
    maxValue: maxCheck ? maxCheck.value : undefined,
  };
};

export function VadPrefixPaddingSelector({
  form,
  schema,
  ...props
}: ConfigurationFormFieldProps) {
  const { minValue, maxValue } = getMinMaxForField(
    ConfigurationFormSchema.shape.vadPrefixPaddingMs,
  );

  const [isHovered, setIsHovered] = React.useState<boolean>(false);

  return (
    <div
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <FormField
        control={form.control}
        name="vadPrefixPaddingMs"
        render={({ field }) => (
          <HoverCard openDelay={200}>
            <HoverCardTrigger asChild>
              <FormItem>
                <div className="flex items-center justify-between">
                  <FormLabel className="text-sm">Prefix Padding (ms)</FormLabel>
                  <FormControl>
                    <Input
                      {...field}
                      className={`shadow-none font-light py-0 h-8 max-w-[100px] text-right ${
                        isHovered ? " border" : " border-none"
                      }`}
                    />
                  </FormControl>
                </div>
                <FormControl>
                  <Slider
                    max={maxValue}
                    min={minValue}
                    defaultValue={[
                      form.formState.defaultValues!.vadPrefixPaddingMs!,
                    ]}
                    step={10}
                    onValueChange={(v) => field.onChange(v[0])}
                    value={[field.value]}
                    className="[&_[role=slider]]:h-4 [&_[role=slider]]:w-4"
                    aria-label="VAD Prefix Padding"
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            </HoverCardTrigger>
            <HoverCardContent
              align="start"
              className="w-[260px] text-sm"
              side="bottom"
            >
              How much audio to include in the audio stream before the speaking
              activation.
            </HoverCardContent>
          </HoverCard>
        )}
      />
    </div>
  );
}

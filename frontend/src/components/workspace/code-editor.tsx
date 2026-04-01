"use client";

import dynamic from "next/dynamic";
import { useTheme } from "next-themes";
import { useMemo } from "react";

import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

import { useThread } from "./messages/context";

const LazyCodeMirror = dynamic(
  () =>
    Promise.all([
      import("@uiw/react-codemirror"),
      import("@uiw/codemirror-theme-monokai"),
      import("@uiw/codemirror-theme-basic"),
      import("@codemirror/lang-css"),
      import("@codemirror/lang-html"),
      import("@codemirror/lang-javascript"),
      import("@codemirror/lang-json"),
      import("@codemirror/lang-markdown"),
      import("@codemirror/lang-python"),
      import("@codemirror/language-data"),
    ]).then(
      ([
        codeMirrorMod,
        monokaiMod,
        basicMod,
        cssMod,
        htmlMod,
        jsMod,
        jsonMod,
        mdMod,
        pythonMod,
        langDataMod,
      ]) => {
        const CodeMirror = codeMirrorMod.default;
        const customDarkTheme = monokaiMod.monokaiInit({
          settings: {
            background: "transparent",
            gutterBackground: "transparent",
            gutterForeground: "#555",
            gutterActiveForeground: "#fff",
            fontSize: "var(--text-sm)",
          },
        });
        const customLightTheme = basicMod.basicLightInit({
          settings: {
            background: "transparent",
            fontSize: "var(--text-sm)",
          },
        });

        function InnerCodeMirror(props: {
          value: string;
          readonly?: boolean;
          disabled?: boolean;
          placeholder?: string;
          autoFocus?: boolean;
          settings?: unknown;
          resolvedTheme?: string;
          className?: string;
        }) {
          const extensions = useMemo(() => {
            return [
              cssMod.css(),
              htmlMod.html(),
              jsMod.javascript({}),
              jsonMod.json(),
              mdMod.markdown({
                base: mdMod.markdownLanguage,
                codeLanguages: langDataMod.languages,
              }),
              pythonMod.python(),
            ];
          }, []);

          return (
            <CodeMirror
              readOnly={props.readonly ?? props.disabled}
              placeholder={props.placeholder}
              className={props.className}
              theme={
                props.resolvedTheme === "dark"
                  ? customDarkTheme
                  : customLightTheme
              }
              extensions={extensions}
              basicSetup={{
                foldGutter:
                  (props.settings as { foldGutter?: boolean })?.foldGutter ??
                  false,
                highlightActiveLine: false,
                highlightActiveLineGutter: false,
                lineNumbers:
                  (props.settings as { lineNumbers?: boolean })?.lineNumbers ??
                  false,
              }}
              autoFocus={props.autoFocus}
              value={props.value}
            />
          );
        }

        return InnerCodeMirror;
      },
    ),
  { ssr: false },
);

export function CodeEditor({
  className,
  placeholder,
  value,
  readonly,
  disabled,
  autoFocus,
  settings,
}: {
  className?: string;
  placeholder?: string;
  value: string;
  readonly?: boolean;
  disabled?: boolean;
  autoFocus?: boolean;
  settings?: unknown;
}) {
  const {
    thread: { isLoading },
  } = useThread();
  const { resolvedTheme } = useTheme();

  return (
    <div
      className={cn(
        "flex cursor-text flex-col overflow-hidden rounded-md",
        className,
      )}
    >
      {isLoading ? (
        <Textarea
          className={cn(
            "h-full overflow-auto font-mono [&_.cm-editor]:h-full [&_.cm-focused]:outline-none!",
            "resize-none p-4! [&_.cm-line]:px-2! [&_.cm-line]:py-0!",
            "border-none",
          )}
          readOnly
          value={value}
        />
      ) : (
        <LazyCodeMirror
          readonly={readonly}
          disabled={disabled}
          placeholder={placeholder}
          className={cn(
            "h-full overflow-auto font-mono [&_.cm-editor]:h-full [&_.cm-focused]:outline-none!",
            "px-2 py-0! [&_.cm-line]:px-2! [&_.cm-line]:py-0!",
          )}
          resolvedTheme={resolvedTheme}
          settings={settings}
          autoFocus={autoFocus}
          value={value}
        />
      )}
    </div>
  );
}

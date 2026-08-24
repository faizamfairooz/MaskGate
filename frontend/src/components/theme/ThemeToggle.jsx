import React from "react"
import { Moon, Sun } from "lucide-react"
import { useTheme } from "./ThemeProvider"
import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()

  const toggleTheme = () => {
    setTheme(theme === "dark" ? "light" : "dark")
  }

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleTheme}
            className="h-8 w-8 text-muted-foreground hover:text-foreground"
            aria-label="Toggle light/dark theme"
          >
            {theme === "dark" ? (
              <Sun className="h-4 w-4 transition-all" />
            ) : (
              <Moon className="h-4 w-4 transition-all" />
            )}
          </Button>
        </TooltipTrigger>
        <TooltipContent side="bottom">
          <span>Switch to {theme === "dark" ? "light" : "dark"} mode</span>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

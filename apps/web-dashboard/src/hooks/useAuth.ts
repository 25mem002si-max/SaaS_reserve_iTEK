import { useEffect, useState } from "react";
import { getToken } from "@/lib/auth";

export function useAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    setIsAuthenticated(Boolean(getToken()));
  }, []);

  return { isAuthenticated };
}

import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useGameStore } from "../store";

/** Route guard configuration */
interface RouteGuardConfig {
  /** Routes that require an active game (saveId + view) */
  requiresActiveGame?: boolean;
  /** Routes that require the game to be over */
  requiresGameOver?: boolean;
  /** Routes that require the game NOT to be over */
  requiresGameNotOver?: boolean;
  /** Redirect target when guard fails */
  fallback?: string;
}

/**
 * Simple route guard hook.
 * Uses Zustand store state to determine if the current route is accessible.
 * Redirects to fallback if guard conditions are not met.
 */
export function useRouteGuard(config: RouteGuardConfig): void {
  const navigate = useNavigate();
  const { saveId, view, loading } = useGameStore();

  useEffect(() => {
    const fallback = config.fallback ?? "/";

    if (config.requiresActiveGame) {
      if (!saveId) {
        navigate("/case-select", { replace: true });
        return;
      }
      if (!view && !loading) {
        navigate("/case-select", { replace: true });
        return;
      }
    }

    if (config.requiresGameOver && view && !view.game_over) {
      navigate("/game", { replace: true });
      return;
    }

    if (config.requiresGameNotOver && view?.game_over) {
      navigate(fallback, { replace: true });
      return;
    }
  }, [
    saveId,
    view,
    loading,
    navigate,
    config.requiresActiveGame,
    config.requiresGameOver,
    config.requiresGameNotOver,
    config.fallback,
  ]);
}

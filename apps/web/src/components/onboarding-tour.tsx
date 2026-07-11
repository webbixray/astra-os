'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';

interface TourStep {
  id: string;
  title: string;
  description: string;
  target: string;
  position: 'top' | 'bottom' | 'left' | 'right';
}

const TOUR_STEPS: TourStep[] = [
  {
    id: 'welcome',
    title: 'Welcome to Astra OS!',
    description: 'This tour will guide you through the key features of your new marketing platform.',
    target: '[data-tour="logo"]',
    position: 'bottom',
  },
  {
    id: 'navigation',
    title: 'Navigation',
    description: 'Use the sidebar to navigate between different sections of the platform.',
    target: '[data-tour="sidebar"]',
    position: 'right',
  },
  {
    id: 'dashboard',
    title: 'Dashboard',
    description: 'Your main hub showing key metrics, recent activity, and quick actions.',
    target: '[data-tour="dashboard"]',
    position: 'bottom',
  },
  {
    id: 'campaigns',
    title: 'Campaigns',
    description: 'Create and manage your marketing campaigns across all channels.',
    target: '[data-tour="campaigns"]',
    position: 'right',
  },
  {
    id: 'ai-assistant',
    title: 'AI Assistant',
    description: 'Press Cmd+K to open the AI assistant for quick commands and content generation.',
    target: '[data-tour="ai-assistant"]',
    position: 'left',
  },
  {
    id: 'notifications',
    title: 'Notifications',
    description: 'Stay updated with real-time notifications about your campaigns and team activity.',
    target: '[data-tour="notifications"]',
    position: 'bottom',
  },
];

const TOUR_COMPLETED_KEY = 'astra_tour_completed';

export function OnboardingTour() {
  const [isActive, setIsActive] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [tooltipPosition, setTooltipPosition] = useState({ top: 0, left: 0 });

  useEffect(() => {
    const completed = localStorage.getItem(TOUR_COMPLETED_KEY);
    if (!completed) {
      const timer = setTimeout(() => {
        setIsActive(true);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, []);

  useEffect(() => {
    if (!isActive) return;

    const step = TOUR_STEPS[currentStep];
    if (!step) return;

    const targetElement = document.querySelector(step.target);
    if (!targetElement) return;

    const rect = targetElement.getBoundingClientRect();
    const scrollTop = window.scrollY;
    const scrollLeft = window.scrollX;

    let top = 0;
    let left = 0;

    switch (step.position) {
      case 'top':
        top = rect.top + scrollTop - 10;
        left = rect.left + scrollLeft + rect.width / 2;
        break;
      case 'bottom':
        top = rect.bottom + scrollTop + 10;
        left = rect.left + scrollLeft + rect.width / 2;
        break;
      case 'left':
        top = rect.top + scrollTop + rect.height / 2;
        left = rect.left + scrollLeft - 10;
        break;
      case 'right':
        top = rect.top + scrollTop + rect.height / 2;
        left = rect.right + scrollLeft + 10;
        break;
    }

    setTooltipPosition({ top, left });

    targetElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, [isActive, currentStep]);

  const handleNext = () => {
    if (currentStep < TOUR_STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      completeTour();
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const completeTour = () => {
    localStorage.setItem(TOUR_COMPLETED_KEY, 'true');
    setIsActive(false);
    setCurrentStep(0);
  };

  const restartTour = () => {
    localStorage.removeItem(TOUR_COMPLETED_KEY);
    setCurrentStep(0);
    setIsActive(true);
  };

  if (!isActive) {
    return (
      <button
        onClick={restartTour}
        className="fixed bottom-4 left-4 z-50 rounded-full bg-primary p-3 text-primary-foreground shadow-lg hover:bg-primary/90"
        title="Restart Tour"
      >
        ?
      </button>
    );
  }

  const step = TOUR_STEPS[currentStep];
  if (!step) return null;

  const positionStyles: React.CSSProperties = {
    position: 'absolute',
    top: tooltipPosition.top,
    left: tooltipPosition.left,
    transform:
      step.position === 'bottom'
        ? 'translateX(-50%)'
        : step.position === 'top'
          ? 'translateX(-50%) translateY(-100%)'
          : step.position === 'right'
            ? 'translateY(-50%)'
            : 'translateY(-50%) translateX(-100%)',
    zIndex: 1000,
  };

  return (
    <>
      <div className="fixed inset-0 z-50 bg-black/50" onClick={completeTour} />
      <div
        className="fixed z-50 w-80 rounded-lg border bg-card p-6 shadow-xl"
        style={positionStyles}
      >
        <div className="mb-4">
          <span className="text-sm text-muted-foreground">
            Step {currentStep + 1} of {TOUR_STEPS.length}
          </span>
        </div>
        <h3 className="mb-2 text-lg font-semibold">{step.title}</h3>
        <p className="mb-6 text-sm text-muted-foreground">{step.description}</p>
        <div className="flex items-center justify-between">
          <Button variant="ghost" size="sm" onClick={completeTour}>
            Skip
          </Button>
          <div className="flex gap-2">
            {currentStep > 0 && (
              <Button variant="outline" size="sm" onClick={handlePrev}>
                Back
              </Button>
            )}
            <Button size="sm" onClick={handleNext}>
              {currentStep === TOUR_STEPS.length - 1 ? 'Finish' : 'Next'}
            </Button>
          </div>
        </div>
      </div>
    </>
  );
}

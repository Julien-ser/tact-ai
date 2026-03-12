import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { Timeline, TimelineTask, quadrantColors } from '../types';

interface TimelineViewProps {
  timeline: Timeline;
  width?: number;
  height?: number;
}

const TimelineView: React.FC<TimelineViewProps> = ({
  timeline,
  width = 800,
  height = 600,
}) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!timeline || !timeline.tasks || timeline.tasks.length === 0) {
      return;
    }

    // Clear previous content
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    // Prepare data
    const tasks: (TimelineTask & { task: any })[] = timeline.tasks
      .filter(tt => tt.task)
      .map(tt => ({
        ...tt,
        task: tt.task!,
      }))
      .sort((a, b) => new Date(a.scheduled_start).getTime() - new Date(b.scheduled_start).getTime());

    if (tasks.length === 0) return;

    const margin = { top: 40, right: 120, bottom: 40, left: 150 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    // Time scale
    const startTime = new Date(d3.min(tasks, d => d.scheduled_start) || timeline.start_date);
    const endTime = new Date(d3.max(tasks, d => d.scheduled_end) || timeline.end_date);
    const timeScale = d3.scaleTime()
      .domain([startTime, endTime])
      .range([0, innerWidth]);

    // Y scale (tasks)
    const taskNames = tasks.map(d => d.task.title);
    const yScale = d3.scaleBand<string>()
      .domain(taskNames)
      .range([0, innerHeight])
      .padding(0.2);

    // Create group
    const g = svg
      .attr('width', width)
      .attr('height', height)
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Grid lines (time)
    const timeTicks = timeScale.ticks(d3.timeHour.every(1));
    g.selectAll('.grid-line')
      .data(timeTicks)
      .enter()
      .append('line')
      .attr('class', 'grid-line')
      .attr('x1', d => timeScale(d))
      .attr('x2', d => timeScale(d))
      .attr('y1', 0)
      .attr('y2', innerHeight)
      .attr('stroke', '#e5e7eb')
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', '3,3');

    // Task rectangles
    g.selectAll('.task-bar')
      .data(tasks)
      .enter()
      .append('rect')
      .attr('class', 'task-bar')
      .attr('x', d => timeScale(new Date(d.scheduled_start)))
      .attr('y', d => yScale(d.task.title) || 0)
      .attr('width', d => {
        const start = new Date(d.scheduled_start).getTime();
        const end = new Date(d.scheduled_end).getTime();
        return Math.max(2, timeScale(new Date(end)) - timeScale(new Date(start)));
      })
      .attr('height', yScale.bandwidth())
      .attr('rx', 4)
      .attr('fill', d => {
        const colors: Record<string, string> = {
          Q1: '#fca5a5',
          Q2: '#86efac',
          Q3: '#fde047',
          Q4: '#d1d5db',
        };
        return colors[d.task.quadrant] || '#d1d5db';
      })
      .attr('stroke', d => {
        const colors: Record<string, string> = {
          Q1: '#dc2626',
          Q2: '#16a34a',
          Q3: '#eab308',
          Q4: '#6b7280',
        };
        return colors[d.task.quadrant] || '#6b7280';
      })
      .attr('stroke-width', 1)
      .on('mouseover', function(event, d) {
        d3.select(this).attr('opacity', 0.8);
      })
      .on('mouseout', function() {
        d3.select(this).attr('opacity', 1);
      });

    // Tooltip (simple title for now)
    g.selectAll('.task-bar')
      .append('title')
      .text(d => `${d.task.title}\n${new Date(d.scheduled_start).toLocaleTimeString()} - ${new Date(d.scheduled_end).toLocaleTimeString()}`);

    // Y-axis (task names)
    g.selectAll('.task-label')
      .data(tasks)
      .enter()
      .append('text')
      .attr('class', 'task-label')
      .attr('x', -10)
      .attr('y', d => (yScale(d.task.title) || 0) + yScale.bandwidth() / 2)
      .attr('text-anchor', 'end')
      .attr('alignment-baseline', 'middle')
      .attr('font-size', '12px')
      .attr('fill', '#374151')
      .text(d => {
        const maxLength = 20;
        const title = d.task.title.length > maxLength
          ? d.task.title.substring(0, maxLength) + '...'
          : d.task.title;
        return title;
      });

    // X-axis
    const xAxis = d3.axisBottom(timeScale)
      .ticks(d3.timeHour.every(2))
      .tickFormat(d3.timeFormat('%H:%M'));

    g.append('g')
      .attr('class', 'x-axis')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(xAxis)
      .selectAll('text')
      .attr('font-size', '11px');

    // Header title
    svg.append('text')
      .attr('x', width / 2)
      .attr('y', 20)
      .attr('text-anchor', 'middle')
      .attr('font-size', '16px')
      .attr('font-weight', 'bold')
      .attr('fill', '#111827')
      .text(`Timeline: ${timeline.name || 'Schedule'}`);

    // Time range label
    const dateRange = `${new Date(timeline.start_date).toLocaleDateString()} - ${new Date(timeline.end_date).toLocaleDateString()}`;
    svg.append('text')
      .attr('x', width / 2)
      .attr('y', height - 10)
      .attr('text-anchor', 'middle')
      .attr('font-size', '12px')
      .attr('fill', '#6b7280')
      .text(dateRange);

  }, [timeline, width, height]);

  if (!timeline || !timeline.tasks || timeline.tasks.length === 0) {
    return (
      <div className="flex items-center justify-center bg-gray-50 rounded-lg border border-gray-200" style={{ width, height }}>
        <p className="text-gray-500">No timeline data available</p>
      </div>
    );
  }

  return (
    <div className="overflow-auto">
      <svg ref={svgRef}></svg>
    </div>
  );
};

export default TimelineView;

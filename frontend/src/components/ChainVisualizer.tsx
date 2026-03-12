import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { Task, TaskChain, quadrantColors } from '../types';

interface ChainVisualizerProps {
  tasks: Task[];
  taskChains: TaskChain[];
  width?: number;
  height?: number;
}

interface NodeData {
  id: number;
  task: Task;
  x?: number;
  y?: number;
}

interface LinkData {
  source: number;
  target: number;
  relationshipType: string;
}

const ChainVisualizer: React.FC<ChainVisualizerProps> = ({
  tasks,
  taskChains,
  width = 800,
  height = 600,
}) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!tasks || tasks.length === 0 || !taskChains || taskChains.length === 0) {
      return;
    }

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    // Create node map for easy lookup
    const taskMap = new Map<number, Task>();
    tasks.forEach(task => taskMap.set(task.id, task));

    // Prepare nodes
    const nodes: NodeData[] = taskChains
      .filter(tc => taskMap.has(tc.task_id) && taskMap.has(tc.prerequisite_task_id))
      .flatMap(tc => [
        { id: tc.task_id, task: taskMap.get(tc.task_id)! },
        { id: tc.prerequisite_task_id, task: taskMap.get(tc.prerequisite_task_id)! }
      ]);

    // Deduplicate nodes
    const uniqueNodes = Array.from(new Map(nodes.map(n => [n.id, n])).values());

    // Prepare links
    const links: LinkData[] = taskChains
      .filter(tc => taskMap.has(tc.task_id) && taskMap.has(tc.prerequisite_task_id))
      .map(tc => ({
        source: tc.prerequisite_task_id,
        target: tc.task_id,
        relationshipType: tc.relationship_type,
      }));

    if (uniqueNodes.length === 0 || links.length === 0) {
      return;
    }

    // Create simulation
    const simulation = d3.forceSimulation(uniqueNodes as any)
      .force('link', d3.forceLink(links).id((d: any) => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('x', d3.forceX(width / 2).strength(0.1))
      .force('y', d3.forceY(height / 2).strength(0.1));

    // Add arrow markers for different relationship types
    const defs = svg.append('defs');

    const relationshipStyles = [
      { type: 'depends_on', color: '#3b82f6', label: '→' },
      { type: 'blocks', color: '#ef4444', label: '⊘' },
      { type: 'relates_to', color: '#8b5cf6', label: '⇄' },
    ];

    relationshipStyles.forEach(style => {
      const marker = defs.append('marker')
        .attr('id', `arrow-${style.type}`)
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 20)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', style.color);
    });

    // Create container group
    const g = svg
      .attr('width', width)
      .attr('height', height)
      .append('g')
      .attr('transform', 'translate(0,0)');

    // Add zoom and pan capabilities
    const zoom = d3.zoom()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom as any);

    // Draw links
    const link = g.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(links)
      .enter()
      .append('line')
      .attr('stroke', d => {
        const style = relationshipStyles.find(s => s.type === d.relationshipType);
        return style ? style.color : '#6b7280';
      })
      .attr('stroke-width', 2)
      .attr('stroke-opacity', 0.6)
      .attr('marker-end', d => `url(#arrow-${d.relationshipType})`);

    // Create node groups
    const node = g.append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(uniqueNodes)
      .enter()
      .append('g')
      .attr('class', 'node')
      .call(d3.drag()
        .on('start', dragStarted)
        .on('drag', dragged)
        .on('end', dragEnded) as any);

    // Draw node circles with quadrant colors
    node.append('circle')
      .attr('r', 25)
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
      .attr('stroke-width', 2);

    // Add task title (truncated)
    node.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '.35em')
      .attr('font-size', '10px')
      .attr('font-weight', 'bold')
      .attr('fill', '#1f2937')
      .text(d => {
        const maxLength = 15;
        return d.task.title.length > maxLength
          ? d.task.title.substring(0, maxLength) + '…'
          : d.task.title;
      });

    // Add priority badge
    node.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '1.5em')
      .attr('font-size', '9px')
      .attr('fill', '#6b7280')
      .text(d => d.task.priority.toUpperCase());

    // Add tooltip behavior
    node.append('title')
      .text(d => {
        const chain = taskChains.find(
          tc => tc.task_id === d.id || tc.prerequisite_task_id === d.id
        );
        return `${d.task.title}\nQuadrant: ${d.task.quadrant}\nPriority: ${d.task.priority}\n${chain ? `Relationship: ${chain.relationship_type}` : ''}`;
      });

    // Position nodes on tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      node.attr('transform', (d: any) => `translate(${d.x},${d.y})`);
    });

    // Drag functions
    function dragStarted(event: any, d: NodeData) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event: any, d: NodeData) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragEnded(event: any, d: NodeData) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    // Cleanup
    return () => {
      simulation.stop();
    };
  }, [tasks, taskChains, width, height]);

  if (!tasks || tasks.length === 0 || !taskChains || taskChains.length === 0) {
    return (
      <div className="flex items-center justify-center bg-gray-50 rounded-lg border border-gray-200" style={{ width, height }}>
        <p className="text-gray-500">No task chains to visualize</p>
      </div>
    );
  }

  return (
    <div className="overflow-auto">
      <svg ref={svgRef}></svg>
    </div>
  );
};

export default ChainVisualizer;

"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  ChevronDown,
  ChevronRight,
  Shield,
  AlertTriangle,
  AlertCircle,
  CheckCircle,
  Zap,
  Target,
  Wrench,
  FileText,
} from "lucide-react";

import {
  getCategories,
  getTestTypes,
  listTestCases,
  type Category,
  type TestCase,
  type TestType,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

interface TestCasesDashboardProps {
  projectId: number;
}

export function TestCasesDashboard({ projectId }: TestCasesDashboardProps) {
  const [selectedCategory, setSelectedCategory] = React.useState<number | null>(
    null,
  );
  const [selectedTestType, setSelectedTestType] = React.useState<number | null>(
    null,
  );
  const [expandedRows, setExpandedRows] = React.useState<Set<number>>(
    new Set(),
  );

  const { data: categories, isLoading: categoriesLoading } = useQuery({
    queryKey: ["categories"],
    queryFn: getCategories,
  });

  const { data: testTypes, isLoading: testTypesLoading } = useQuery({
    queryKey: ["test-types"],
    queryFn: getTestTypes,
  });

  const { data: testCases, isLoading: casesLoading } = useQuery({
    queryKey: ["test-cases", selectedCategory, selectedTestType],
    queryFn: () =>
      listTestCases(
        selectedCategory ?? undefined,
        selectedTestType ?? undefined,
      ),
  });

  const toggleRow = (testCaseId: number) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(testCaseId)) {
      newExpanded.delete(testCaseId);
    } else {
      newExpanded.add(testCaseId);
    }
    setExpandedRows(newExpanded);
  };

  const selectedCategoryName = categories?.find(
    (c) => c.id === selectedCategory,
  )?.name;
  const selectedTestTypeName = testTypes?.find(
    (t) => t.id === selectedTestType,
  )?.name;

  const isLoading = categoriesLoading || testTypesLoading || casesLoading;

  const getSeverityColor = (rank: number) => {
    if (rank >= 4)
      return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
    if (rank === 3)
      return "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200";
    if (rank === 2)
      return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200";
    return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
  };

  const getSeverityIcon = (rank: number) => {
    if (rank >= 4) return <AlertTriangle className="h-3 w-3" />;
    if (rank === 3) return <AlertCircle className="h-3 w-3" />;
    if (rank === 2) return <Zap className="h-3 w-3" />;
    return <CheckCircle className="h-3 w-3" />;
  };

  return (
    <div className="space-y-6">
      <Card className="border-l-4 border-l-blue-500 shadow-sm">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-blue-600" />
            <CardTitle>Security Test Cases</CardTitle>
          </div>
          <CardDescription>
            Browse and filter comprehensive test cases by category and type
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3 flex-wrap items-end">
            <div className="space-y-2">
              <p className="text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wide">
                Category
              </p>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="outline"
                    className="w-48 bg-gradient-to-r from-blue-50 to-blue-50/50 dark:from-blue-950/30 dark:to-blue-950/20 border-blue-200 dark:border-blue-800 hover:border-blue-400 dark:hover:border-blue-600"
                  >
                    {selectedCategoryName ? (
                      <span className="flex items-center gap-2">
                        <Target className="h-3.5 w-3.5" />
                        {selectedCategoryName}
                      </span>
                    ) : (
                      "Select Category"
                    )}
                    <ChevronDown className="ml-auto h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start" className="w-48">
                  <DropdownMenuCheckboxItem
                    checked={selectedCategory === null}
                    onCheckedChange={() => setSelectedCategory(null)}
                  >
                    All Categories
                  </DropdownMenuCheckboxItem>
                  {categories?.map((category) => (
                    <DropdownMenuCheckboxItem
                      key={category.id}
                      checked={selectedCategory === category.id}
                      onCheckedChange={() => setSelectedCategory(category.id)}
                    >
                      {category.name}
                    </DropdownMenuCheckboxItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>
            </div>

            <div className="space-y-2">
              <p className="text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wide">
                Test Type
              </p>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="outline"
                    className="w-48 bg-gradient-to-r from-purple-50 to-purple-50/50 dark:from-purple-950/30 dark:to-purple-950/20 border-purple-200 dark:border-purple-800 hover:border-purple-400 dark:hover:border-purple-600"
                  >
                    {selectedTestTypeName ? (
                      <span className="flex items-center gap-2">
                        <Wrench className="h-3.5 w-3.5" />
                        {selectedTestTypeName}
                      </span>
                    ) : (
                      "Select Test Type"
                    )}
                    <ChevronDown className="ml-auto h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start" className="w-48">
                  <DropdownMenuCheckboxItem
                    checked={selectedTestType === null}
                    onCheckedChange={() => setSelectedTestType(null)}
                  >
                    All Test Types
                  </DropdownMenuCheckboxItem>
                  {testTypes?.map((testType) => (
                    <DropdownMenuCheckboxItem
                      key={testType.id}
                      checked={selectedTestType === testType.id}
                      onCheckedChange={() => setSelectedTestType(testType.id)}
                    >
                      {testType.name}
                    </DropdownMenuCheckboxItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="border shadow-sm">
        {isLoading ? (
          <div className="space-y-3 p-6">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-12 w-full" />
              </div>
            ))}
          </div>
        ) : testCases && testCases.length > 0 ? (
          <div className="overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="bg-gradient-to-r from-slate-50 to-slate-50 dark:from-slate-900 dark:to-slate-800 border-b-2 border-slate-200 dark:border-slate-700">
                  <TableHead className="w-8 text-slate-700 dark:text-slate-300 font-semibold"></TableHead>
                  <TableHead className="w-1/4 text-slate-700 dark:text-slate-300 font-semibold">
                    Test Case
                  </TableHead>
                  <TableHead className="text-slate-700 dark:text-slate-300 font-semibold">
                    Category
                  </TableHead>
                  <TableHead className="text-slate-700 dark:text-slate-300 font-semibold">
                    Type
                  </TableHead>
                  <TableHead className="text-slate-700 dark:text-slate-300 font-semibold">
                    Severity
                  </TableHead>
                  <TableHead className="text-slate-700 dark:text-slate-300 font-semibold">
                    Asset
                  </TableHead>
                  <TableHead className="text-right text-slate-700 dark:text-slate-300 font-semibold">
                    Actions
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {testCases.map((testCase, index) => (
                  <React.Fragment key={testCase.id}>
                    <TableRow
                      className={`cursor-pointer transition-colors ${
                        index % 2 === 0
                          ? "bg-white dark:bg-slate-950"
                          : "bg-slate-50 dark:bg-slate-900/50"
                      } hover:bg-blue-50 dark:hover:bg-blue-950/30 border-b border-slate-100 dark:border-slate-800`}
                      onClick={() => toggleRow(testCase.id)}
                    >
                      <TableCell className="pl-4">
                        <div className="text-blue-600 dark:text-blue-400">
                          {expandedRows.has(testCase.id) ? (
                            <ChevronDown className="h-4 w-4" />
                          ) : (
                            <ChevronRight className="h-4 w-4" />
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="font-semibold text-slate-900 dark:text-slate-100">
                        <div className="line-clamp-2 text-sm">
                          {testCase.action_test_case}
                        </div>
                      </TableCell>
                      <TableCell>
                        {testCase.category ? (
                          <Badge className="bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200 hover:bg-indigo-200 dark:hover:bg-indigo-800">
                            {testCase.category.name}
                          </Badge>
                        ) : (
                          <span className="text-slate-400">—</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {testCase.test_type ? (
                          <Badge className="bg-cyan-100 text-cyan-800 dark:bg-cyan-900 dark:text-cyan-200 hover:bg-cyan-200 dark:hover:bg-cyan-800">
                            {testCase.test_type.name}
                          </Badge>
                        ) : (
                          <span className="text-slate-400">—</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {testCase.severity ? (
                          <Badge
                            className={`${getSeverityColor(
                              testCase.severity.severity_rank,
                            )} flex items-center gap-1 w-fit`}
                          >
                            {getSeverityIcon(testCase.severity.severity_rank)}
                            {testCase.severity.name}
                          </Badge>
                        ) : (
                          <span className="text-slate-400">—</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {testCase.asset ? (
                          <span className="text-sm text-slate-700 dark:text-slate-300">
                            {testCase.asset.asset_name}
                          </span>
                        ) : (
                          <span className="text-slate-400">—</span>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
                          onClick={(e) => {
                            e.stopPropagation();
                          }}
                        >
                          View
                        </Button>
                      </TableCell>
                    </TableRow>

                    {/* Expandable Details Row */}
                    {expandedRows.has(testCase.id) && (
                      <TableRow className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 border-b-2 border-blue-200 dark:border-blue-900">
                        <TableCell colSpan={7} className="p-0">
                          <div className="p-6 space-y-6">
                            {/* Main Description Section */}
                            {testCase.description && (
                              <div className="bg-blue-50 dark:bg-blue-950/20 border-l-4 border-blue-500 p-4 rounded-r-lg">
                                <div className="flex items-start gap-2">
                                  <FileText className="h-4 w-4 text-blue-600 dark:text-blue-400 mt-1 flex-shrink-0" />
                                  <div className="flex-1">
                                    <p className="text-xs font-semibold text-blue-600 dark:text-blue-400 uppercase tracking-wide mb-2">
                                      Description
                                    </p>
                                    <p className="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap leading-relaxed">
                                      {testCase.description}
                                    </p>
                                  </div>
                                </div>
                              </div>
                            )}

                            {/* Test Steps Section */}
                            {testCase.test_steps && (
                              <div className="bg-purple-50 dark:bg-purple-950/20 border-l-4 border-purple-500 p-4 rounded-r-lg">
                                <div className="flex items-start gap-2">
                                  <Wrench className="h-4 w-4 text-purple-600 dark:text-purple-400 mt-1 flex-shrink-0" />
                                  <div className="flex-1">
                                    <p className="text-xs font-semibold text-purple-600 dark:text-purple-400 uppercase tracking-wide mb-2">
                                      Test Steps
                                    </p>
                                    <p className="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap leading-relaxed">
                                      {testCase.test_steps}
                                    </p>
                                  </div>
                                </div>
                              </div>
                            )}

                            {/* Expected Output Section */}
                            {testCase.expected_output && (
                              <div className="bg-green-50 dark:bg-green-950/20 border-l-4 border-green-500 p-4 rounded-r-lg">
                                <div className="flex items-start gap-2">
                                  <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400 mt-1 flex-shrink-0" />
                                  <div className="flex-1">
                                    <p className="text-xs font-semibold text-green-600 dark:text-green-400 uppercase tracking-wide mb-2">
                                      Expected Output
                                    </p>
                                    <p className="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap leading-relaxed">
                                      {testCase.expected_output}
                                    </p>
                                  </div>
                                </div>
                              </div>
                            )}

                            {/* Attack Information Section */}
                            {(testCase.attack_path ||
                              testCase.attack_feasibility) && (
                              <div className="bg-red-50 dark:bg-red-950/20 border-l-4 border-red-500 p-4 rounded-r-lg space-y-3">
                                <div className="flex items-start gap-2">
                                  <AlertTriangle className="h-4 w-4 text-red-600 dark:text-red-400 mt-1 flex-shrink-0" />
                                  <div className="flex-1 space-y-3">
                                    <p className="text-xs font-semibold text-red-600 dark:text-red-400 uppercase tracking-wide">
                                      Attack Information
                                    </p>
                                    {testCase.attack_path && (
                                      <div>
                                        <p className="text-xs font-medium text-red-700 dark:text-red-300 mb-1">
                                          Attack Path
                                        </p>
                                        <p className="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap">
                                          {testCase.attack_path}
                                        </p>
                                      </div>
                                    )}
                                    {testCase.attack_feasibility && (
                                      <div>
                                        <p className="text-xs font-medium text-red-700 dark:text-red-300 mb-1">
                                          Attack Feasibility
                                        </p>
                                        <p className="text-sm text-slate-700 dark:text-slate-300">
                                          {testCase.attack_feasibility}
                                        </p>
                                      </div>
                                    )}
                                  </div>
                                </div>
                              </div>
                            )}

                            {/* Impact Analysis Grid */}
                            <div className="grid grid-cols-2 gap-4">
                              {testCase.cia_impact && (
                                <div className="bg-orange-50 dark:bg-orange-950/20 border-l-4 border-orange-500 p-3 rounded-r">
                                  <p className="text-xs font-semibold text-orange-600 dark:text-orange-400 uppercase tracking-wide mb-1">
                                    CIA Impact
                                  </p>
                                  <p className="text-sm text-slate-700 dark:text-slate-300">
                                    {testCase.cia_impact}
                                  </p>
                                </div>
                              )}

                              {testCase.safety_impact && (
                                <div className="bg-pink-50 dark:bg-pink-950/20 border-l-4 border-pink-500 p-3 rounded-r">
                                  <p className="text-xs font-semibold text-pink-600 dark:text-pink-400 uppercase tracking-wide mb-1">
                                    Safety Impact
                                  </p>
                                  <p className="text-sm text-slate-700 dark:text-slate-300">
                                    {testCase.safety_impact}
                                  </p>
                                </div>
                              )}

                              {testCase.automation_possible && (
                                <div className="bg-teal-50 dark:bg-teal-950/20 border-l-4 border-teal-500 p-3 rounded-r">
                                  <p className="text-xs font-semibold text-teal-600 dark:text-teal-400 uppercase tracking-wide mb-1">
                                    Automation
                                  </p>
                                  <p className="text-sm text-slate-700 dark:text-slate-300">
                                    {testCase.automation_possible}
                                  </p>
                                </div>
                              )}

                              {testCase.protocol && (
                                <div className="bg-indigo-50 dark:bg-indigo-950/20 border-l-4 border-indigo-500 p-3 rounded-r">
                                  <p className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 uppercase tracking-wide mb-1">
                                    Protocol
                                  </p>
                                  <p className="text-sm text-slate-700 dark:text-slate-300">
                                    {testCase.protocol.name}
                                  </p>
                                </div>
                              )}
                            </div>

                            {/* Threat and Attack Vector */}
                            <div className="grid grid-cols-2 gap-4">
                              {testCase.threat && (
                                <div className="bg-yellow-50 dark:bg-yellow-950/20 border-l-4 border-yellow-500 p-3 rounded-r">
                                  <p className="text-xs font-semibold text-yellow-600 dark:text-yellow-400 uppercase tracking-wide mb-1">
                                    Threat
                                  </p>
                                  <p className="text-sm text-slate-700 dark:text-slate-300">
                                    {testCase.threat.threat_text}
                                  </p>
                                </div>
                              )}

                              {testCase.attack_vector && (
                                <div className="bg-violet-50 dark:bg-violet-950/20 border-l-4 border-violet-500 p-3 rounded-r">
                                  <p className="text-xs font-semibold text-violet-600 dark:text-violet-400 uppercase tracking-wide mb-1">
                                    Attack Vector
                                  </p>
                                  <p className="text-sm text-slate-700 dark:text-slate-300">
                                    {testCase.attack_vector.name}
                                  </p>
                                </div>
                              )}
                            </div>

                            {/* Tools Section */}
                            {testCase.test_case_tools.length > 0 && (
                              <div className="bg-slate-200/30 dark:bg-slate-700/30 p-4 rounded-lg border border-slate-300 dark:border-slate-600">
                                <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wide mb-3">
                                  <Wrench className="inline-block h-3 w-3 mr-1" />
                                  Tools Used
                                </p>
                                <div className="flex flex-wrap gap-2">
                                  {testCase.test_case_tools.map((tool, idx) => (
                                    <Badge
                                      key={idx}
                                      className="bg-slate-600 text-white dark:bg-slate-400 dark:text-slate-900 hover:bg-slate-700 dark:hover:bg-slate-300"
                                    >
                                      {tool.tool.tool_name}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* References Section */}
                            {testCase.test_case_references.length > 0 && (
                              <div className="bg-slate-200/30 dark:bg-slate-700/30 p-4 rounded-lg border border-slate-300 dark:border-slate-600">
                                <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wide mb-3">
                                  <FileText className="inline-block h-3 w-3 mr-1" />
                                  References
                                </p>
                                <div className="space-y-2">
                                  {testCase.test_case_references.map(
                                    (ref, idx) => (
                                      <div
                                        key={idx}
                                        className="text-sm text-slate-700 dark:text-slate-300 pl-3 border-l-2 border-slate-400 dark:border-slate-600"
                                      >
                                        {ref.reference.ref_text}
                                      </div>
                                    ),
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    )}
                  </React.Fragment>
                ))}
              </TableBody>
            </Table>
          </div>
        ) : (
          <div className="flex items-center justify-center p-16 text-center">
            <div>
              <Shield className="h-12 w-12 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
              <p className="font-semibold text-slate-900 dark:text-slate-100 mb-2">
                No test cases found
              </p>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Try adjusting your filters to find relevant security test cases
              </p>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}

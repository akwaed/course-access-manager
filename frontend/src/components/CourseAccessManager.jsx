import React, { useState, useEffect } from 'react';

const BASE_PATH = '/tcecontacts';
const API_BASE_URL = '/tcecontacts/api';

const CourseAccessManager = ({ user, onLogout }) => {
  const [contacts, setContacts] = useState([]);
  const [courses, setCourses] = useState([]);
  const [hierarchy, setHierarchy] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedView, setSelectedView] = useState('contacts');
  const [searchTerm, setSearchTerm] = useState('');
  const [showProfileMenu, setShowProfileMenu] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      // For now, we'll use placeholder data
      // Replace with actual API calls when backend is ready
      setContacts([
        { id: 1, first_name: 'John', last_name: 'Doe', linkblue: 'jdoe', department: 'Computer Science' },
        { id: 2, first_name: 'Jane', last_name: 'Smith', linkblue: 'jsmith', department: 'Engineering' }
      ]);
      setCourses([
        { SECTION_KEY: 'CS101-001', TITLE: 'Introduction to Computer Science', PREFIX: 'CS', CLASS: '101' },
        { SECTION_KEY: 'CS201-001', TITLE: 'Data Structures', PREFIX: 'CS', CLASS: '201' }
      ]);
      setError(null);
    } catch (err) {
      setError('Failed to load data. Please try again later.');
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
    }
  };

  const generateHierarchyFile = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/generate/hierarchy`, {
        method: 'POST',
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to generate hierarchy file');
      }

      // Get the blob from the response
      const blob = await response.blob();

      // Create a download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'hierarchy.csv';
      document.body.appendChild(a);
      a.click();

      // Cleanup
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      alert('Hierarchy file generated and downloaded successfully!');
    } catch (err) {
      console.error('Error generating hierarchy file:', err);
      alert('Failed to generate hierarchy file. Please try again.');
    }
  };

  const filteredContacts = contacts.filter(contact => 
    contact.first_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    contact.last_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    contact.linkblue?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    contact.department?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredCourses = courses.filter(course =>
    course.SECTION_KEY?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    course.TITLE?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    course.PREFIX?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-800 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-center">
          <p className="text-red-600">{error}</p>
          <button 
            onClick={loadData}
            className="mt-4 px-4 py-2 bg-blue-800 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-blue-800 text-white">
        <div className="container mx-auto px-4 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold">University of Kentucky</h1>
              <h2 className="text-xl mt-2">Course Access Manager</h2>
            </div>
            {/* Profile Button */}
            <div className="relative">
              <button
                onClick={() => setShowProfileMenu(!showProfileMenu)}
                className="flex items-center space-x-2 bg-blue-700 hover:bg-blue-600 px-4 py-2 rounded-lg transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                <span>Hi, {user?.first_name || 'User'}</span>
                <svg className={`w-4 h-4 transition-transform ${showProfileMenu ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              {/* Profile Dropdown Menu */}
              {showProfileMenu && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg py-2 z-50">
                  <div className="px-4 py-2 border-b border-gray-200">
                    <p className="text-sm text-gray-600">Signed in as</p>
                    <p className="text-sm font-semibold text-gray-800">{user?.email}</p>
                    <p className="text-xs text-gray-500 mt-1">{user?.role}</p>
                  </div>
                  <button
                    onClick={() => {
                      setShowProfileMenu(false);
                      onLogout();
                    }}
                    className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-100 flex items-center space-x-2"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                    </svg>
                    <span>Logout</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-blue-700 text-white">
        <div className="container mx-auto px-4">
          <div className="flex space-x-4">
            <button
              onClick={() => setSelectedView('contacts')}
              className={`py-3 px-4 ${selectedView === 'contacts' ? 'bg-blue-800' : 'hover:bg-blue-600'}`}
            >
              Contacts
            </button>
            <button
              onClick={() => setSelectedView('courses')}
              className={`py-3 px-4 ${selectedView === 'courses' ? 'bg-blue-800' : 'hover:bg-blue-600'}`}
            >
              Courses
            </button>
            {/* Files tab - Admin only */}
            {user?.role === 'System Admin' && (
              <button
                onClick={() => setSelectedView('files')}
                className={`py-3 px-4 ${selectedView === 'files' ? 'bg-blue-800' : 'hover:bg-blue-600'}`}
              >
                Files
              </button>
            )}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Search Bar */}
        <div className="mb-6">
          <input
            type="text"
            placeholder={`Search ${selectedView}...`}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Content Display */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          {selectedView === 'contacts' && (
            <div>
              <h3 className="text-2xl font-bold mb-4">Contacts</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">LinkBlue</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Department</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredContacts.map((contact) => (
                      <tr key={contact.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          {contact.first_name} {contact.last_name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-gray-600">
                          {contact.linkblue}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-gray-600">
                          {contact.department}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {selectedView === 'courses' && (
            <div>
              <h3 className="text-2xl font-bold mb-4">Courses</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Section Key</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Title</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Prefix</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Class</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredCourses.map((course, index) => (
                      <tr key={course.SECTION_KEY || index} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap font-medium">
                          {course.SECTION_KEY}
                        </td>
                        <td className="px-6 py-4">
                          {course.TITLE}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-gray-600">
                          {course.PREFIX}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-gray-600">
                          {course.CLASS}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {selectedView === 'files' && user?.role === 'System Admin' && (
            <div>
              <h3 className="text-2xl font-bold mb-4">File Management</h3>
              <p className="text-gray-600 mb-6">Generate auxiliary files from course data</p>

              {/* Hierarchy File Generation */}
              <div className="border border-gray-200 rounded-lg p-6 mb-4">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="text-lg font-semibold mb-2">Course Hierarchy File</h4>
                    <p className="text-sm text-gray-600 mb-4">
                      Generate a comprehensive hierarchy CSV file from the course data.
                      This file includes section details, academic terms, department information, and more.
                    </p>
                    <div className="text-xs text-gray-500">
                      <p>Output columns: SECTION_KEY, TITLE, CANVAS_SIS_ID, CRS_SECTION, PREFIX, CLASS, CLASS_ID, SECTION, SECTION_ID, ACADEMIC_YEAR, ACADEMIC_TERM_ID, ACADEMIC_TERM, SECTION_TITLE, SECTION_BEGIN_DATE, SECTION_END_DATE, SECTION_LENGTH_DAYS, TCE_INVITE, TCE_R1, TCE_R2, TCE_END_DATE, TCE_REPORT_DATE, CLASS_DEPARTMENT, CLASS_DEPARTMENT_ID, CLASS_COLLEGE, CLASS_COLLEGE_SHORT, CLASS_LEVEL, IS_CROSSLISTED, CROSSLISTED_ID, DISTANCE_LEARNING, IS_UK_CORE, UK_CORE_TYPE, SPEC_TYPE</p>
                    </div>
                  </div>
                  <button
                    onClick={() => generateHierarchyFile()}
                    className="px-6 py-2 bg-blue-800 text-white rounded-lg hover:bg-blue-700 transition-colors whitespace-nowrap ml-4"
                  >
                    Generate & Download
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-white mt-12">
        <div className="container mx-auto px-4 py-6 text-center">
          <p>&copy; 2024 University of Kentucky. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default CourseAccessManager;

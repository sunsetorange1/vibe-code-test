// frontend/src/pages/TaskDetailPage.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getTask, getTaskEvidence, addEvidence, updateEvidence } from '../services/api';
import { Container, Row, Col, Button, Table, Spinner, Alert, Card, Form, Modal } from 'react-bootstrap';

function TaskDetailPage() {
  const { projectId, taskId } = useParams(); // projectId for back navigation or context
  const navigate = useNavigate();

  const [task, setTask] = useState(null);
  const [evidenceList, setEvidenceList] = useState([]);
  const [loadingTask, setLoadingTask] = useState(true);
  const [loadingEvidence, setLoadingEvidence] = useState(true);
  const [error, setError] = useState(null);

  // Add Evidence Form State
  const [showAddEvidenceModal, setShowAddEvidenceModal] = useState(false);
  const [newEvidenceFile, setNewEvidenceFile] = useState(null);
  const [newEvidenceNotes, setNewEvidenceNotes] = useState('');
  const [newEvidenceToolType, setNewEvidenceToolType] = useState('');
  const [submittingEvidence, setSubmittingEvidence] = useState(false);

  // Update Evidence Modal State
  const [showUpdateEvidenceModal, setShowUpdateEvidenceModal] = useState(false);
  const [currentEvidence, setCurrentEvidence] = useState(null);
  const [updateEvidenceNotes, setUpdateEvidenceNotes] = useState('');
  const [updateEvidenceVerified, setUpdateEvidenceVerified] = useState(false);
  const [submittingUpdateEvidence, setSubmittingUpdateEvidence] = useState(false);

  const loadTaskDetails = useCallback(async () => {
    try {
      setLoadingTask(true);
      const taskData = await getTask(taskId);
      setTask(taskData);
      setError(null);
    } catch (err) {
      setError(err.message || `Failed to load task details for ID ${taskId}.`);
      setTask(null);
    } finally {
      setLoadingTask(false);
    }
  }, [taskId]);

  const loadEvidence = useCallback(async () => {
    try {
      setLoadingEvidence(true);
      const evidenceData = await getTaskEvidence(taskId);
      setEvidenceList(evidenceData);
    } catch (err) {
      setError(prevError => prevError ? `${prevError}\n${err.message}` : (err.message || `Failed to load evidence for task ID ${taskId}.`));
      setEvidenceList([]);
    } finally {
      setLoadingEvidence(false);
    }
  }, [taskId]);

  useEffect(() => {
    loadTaskDetails();
    loadEvidence();
  }, [loadTaskDetails, loadEvidence]);

  const handleAddEvidenceShow = () => setShowAddEvidenceModal(true);
  const handleAddEvidenceClose = () => {
    setShowAddEvidenceModal(false);
    setNewEvidenceFile(null);
    setNewEvidenceNotes('');
    setNewEvidenceToolType('');
    setError(null); // Clear errors from modal
  };

  const handleFileChange = (e) => {
    setNewEvidenceFile(e.target.files[0]);
  };

  const handleAddEvidenceSubmit = async (e) => {
    e.preventDefault();
    if (!newEvidenceFile) {
      setError("A file is required to add evidence.");
      return;
    }
    setSubmittingEvidence(true);
    setError(null);
    const formData = new FormData();
    formData.append('file', newEvidenceFile);
    formData.append('notes', newEvidenceNotes);
    formData.append('tool_type', newEvidenceToolType);

    try {
      await addEvidence(taskId, formData);
      handleAddEvidenceClose();
      loadEvidence(); // Refresh evidence list
    } catch (err) {
      setError(err.message || "Failed to add evidence.");
    } finally {
      setSubmittingEvidence(false);
    }
  };

  const handleUpdateEvidenceShow = (evidenceItem) => {
    setCurrentEvidence(evidenceItem);
    setUpdateEvidenceNotes(evidenceItem.notes || '');
    setUpdateEvidenceVerified(evidenceItem.verified || false);
    setShowUpdateEvidenceModal(true);
  };
  const handleUpdateEvidenceClose = () => {
    setShowUpdateEvidenceModal(false);
    setCurrentEvidence(null);
    setUpdateEvidenceNotes('');
    setUpdateEvidenceVerified(false);
    setError(null);
  };

  const handleUpdateEvidenceSubmit = async (e) => {
    e.preventDefault();
    if (!currentEvidence) return;
    setSubmittingUpdateEvidence(true);
    setError(null);
    try {
      await updateEvidence(currentEvidence.id, {
        notes: updateEvidenceNotes,
        verified: updateEvidenceVerified,
      });
      handleUpdateEvidenceClose();
      loadEvidence(); // Refresh list
    } catch (err) {
      setError(err.message || "Failed to update evidence.");
    } finally {
      setSubmittingUpdateEvidence(false);
    }
  };


  if (loadingTask) {
    return <Container className="mt-3 text-center"><Spinner animation="border" /><p>Loading task...</p></Container>;
  }

  if (error && !task) {
    return <Container className="mt-3"><Alert variant="danger"><Alert.Heading>Error</Alert.Heading><p>{error}</p></Alert></Container>;
  }

  if (!task) {
    return <Container className="mt-3"><Alert variant="warning">Task not found.</Alert></Container>;
  }

  return (
    <Container className="mt-3">
      <Button variant="outline-secondary" size="sm" onClick={() => navigate(`/projects/${projectId}`)} className="mb-3">
        &laquo; Back to Project
      </Button>
      <Card className="mb-4">
        <Card.Header as="h1">Task: {task.title}</Card.Header>
        <Card.Body>
          <Row>
            <Col md={8}>
              <p><strong>Description:</strong> {task.description || 'N/A'}</p>
            </Col>
            <Col md={4}>
              <p><strong>Status:</strong> {task.status}</p>
              <p><strong>Priority:</strong> {task.priority}</p>
              <p><strong>Due Date:</strong> {task.due_date || 'N/A'}</p>
              <p><strong>Reminder Sent:</strong> {task.due_date_reminder_sent ? 'Yes' : 'No'}</p>
              <p><strong>Assigned To (ID):</strong> {task.assigned_to_id || 'Unassigned'}</p>
              <p><strong>Created At:</strong> {new Date(task.created_at).toLocaleString()}</p>
              <p><strong>Updated At:</strong> {new Date(task.updated_at).toLocaleString()}</p>
            </Col>
          </Row>
        </Card.Body>
      </Card>

      <div className="d-flex justify-content-between align-items-center mb-3">
        <h2>Evidence</h2>
        <Button variant="primary" onClick={handleAddEvidenceShow}>Add Evidence</Button>
      </div>

      {/* General Error Display for page level errors after initial load */}
      {error && <Alert variant="danger" className="mb-3">{error}</Alert>}

      {loadingEvidence && <div className="text-center"><Spinner animation="border" size="sm" /><p>Loading evidence...</p></div>}

      {!loadingEvidence && evidenceList.length === 0 && (
        <Alert variant="info">No evidence submitted for this task yet.</Alert>
      )}

      {!loadingEvidence && evidenceList.length > 0 && (
        <Table striped bordered hover responsive>
          <thead>
            <tr>
              <th>ID</th>
              <th>File Name</th>
              <th>Tool Type</th>
              <th>MIME Type</th>
              <th>Notes</th>
              <th>Uploaded</th>
              <th>Verified</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {evidenceList.map((ev) => (
              <tr key={ev.id}>
                <td>{ev.id}</td>
                <td>
                  <a href={`${API_BASE_URL}/evidence/${ev.id}/download`} target="_blank" rel="noopener noreferrer">
                    {ev.file_name}
                  </a>
                </td>
                <td>{ev.tool_type || 'N/A'}</td>
                <td>{ev.mime_type || 'N/A'}</td>
                <td>{ev.notes || 'N/A'}</td>
                <td>{new Date(ev.upload_date).toLocaleString()}</td>
                <td>{ev.verified ? 'Yes' : 'No'}</td>
                <td>
                  <Button variant="outline-primary" size="sm" onClick={() => handleUpdateEvidenceShow(ev)}>
                    Edit
                  </Button>
                  {/* Future: Delete button */}
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}

      {/* Add Evidence Modal */}
      <Modal show={showAddEvidenceModal} onHide={handleAddEvidenceClose} backdrop="static">
        <Modal.Header closeButton>
          <Modal.Title>Add New Evidence</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {error && <Alert variant="danger">{error}</Alert>}
          <Form onSubmit={handleAddEvidenceSubmit}>
            <Form.Group controlId="evidenceFile" className="mb-3">
              <Form.Label>File <span className="text-danger">*</span></Form.Label>
              <Form.Control type="file" onChange={handleFileChange} required />
            </Form.Group>
            <Form.Group controlId="evidenceToolType" className="mb-3">
              <Form.Label>Tool Type</Form.Label>
              <Form.Control
                type="text"
                placeholder="e.g., Nessus, Screenshot"
                value={newEvidenceToolType}
                onChange={(e) => setNewEvidenceToolType(e.target.value)}
              />
            </Form.Group>
            <Form.Group controlId="evidenceNotes" className="mb-3">
              <Form.Label>Notes</Form.Label>
              <Form.Control
                as="textarea"
                rows={3}
                value={newEvidenceNotes}
                onChange={(e) => setNewEvidenceNotes(e.target.value)}
              />
            </Form.Group>
            <Button variant="secondary" onClick={handleAddEvidenceClose} className="me-2" disabled={submittingEvidence}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" disabled={submittingEvidence}>
              {submittingEvidence ? <><Spinner as="span" animation="border" size="sm" role="status" aria-hidden="true" /> Uploading...</> : 'Upload Evidence'}
            </Button>
          </Form>
        </Modal.Body>
      </Modal>

      {/* Update Evidence Modal */}
      {currentEvidence && (
        <Modal show={showUpdateEvidenceModal} onHide={handleUpdateEvidenceClose} backdrop="static">
          <Modal.Header closeButton>
            <Modal.Title>Update Evidence: {currentEvidence.file_name}</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            {error && <Alert variant="danger">{error}</Alert>}
            <Form onSubmit={handleUpdateEvidenceSubmit}>
              <Form.Group controlId="updateEvidenceNotes" className="mb-3">
                <Form.Label>Notes</Form.Label>
                <Form.Control
                  as="textarea"
                  rows={3}
                  value={updateEvidenceNotes}
                  onChange={(e) => setUpdateEvidenceNotes(e.target.value)}
                />
              </Form.Group>
              <Form.Group controlId="updateEvidenceVerified" className="mb-3">
                <Form.Check
                  type="switch"
                  label="Verified Evidence"
                  checked={updateEvidenceVerified}
                  onChange={(e) => setUpdateEvidenceVerified(e.target.checked)}
                />
              </Form.Group>
              <Button variant="secondary" onClick={handleUpdateEvidenceClose} className="me-2" disabled={submittingUpdateEvidence}>
                Cancel
              </Button>
              <Button variant="primary" type="submit" disabled={submittingUpdateEvidence}>
                {submittingUpdateEvidence ? <><Spinner as="span" animation="border" size="sm" role="status" aria-hidden="true" /> Saving...</> : 'Save Changes'}
              </Button>
            </Form>
          </Form>
        </Modal.Body>
      </Modal>
      )}
    </Container>
  );
}

export default TaskDetailPage;
